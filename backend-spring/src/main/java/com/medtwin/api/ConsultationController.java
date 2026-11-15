package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.util.*;

/** Paid video consultations: booking, room access and the prescription note. */
@RestController
public class ConsultationController {
    private static final double DEFAULT_FEE = 10.00;

    /**
     * How long a paid consultation's room stays enterable (minutes). After the
     * window the consultation is marked EXPIRED and the room option turns off
     * automatically, on both the patient and clinician side.
     */
    private static final int ROOM_VALIDITY_MINUTES = readValidityMinutes();

    private static int readValidityMinutes() {
        try {
            return Math.max(5, Integer.parseInt(System.getenv().getOrDefault("MEDTWIN_ROOM_VALIDITY_MINUTES", "120")));
        } catch (NumberFormatException ignored) {
            return 120;
        }
    }

    /** Mark paid/waiting consultations past their validity window as EXPIRED. */
    private void expireStale() {
        db.exec("UPDATE consultations SET status = 'EXPIRED' "
                + "WHERE status IN ('PAID', 'WAITING_ROOM') "
                + "AND created_at < DATE_SUB(NOW(), INTERVAL ? MINUTE)", ROOM_VALIDITY_MINUTES);
    }
    private static final SecureRandom RANDOM = new SecureRandom();

    private final Db db;
    private final Access access;
    private final Audit audit;
    private final Realtime realtime;

    public ConsultationController(Db db, Access access, Audit audit, Realtime realtime) {
        this.db = db;
        this.access = access;
        this.audit = audit;
        this.realtime = realtime;
    }

    /** Patient books a paid consultation, optionally attached to an appointment. */
    @PostMapping("/consultations/")
    public ResponseEntity<Object> create(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        String doctorId = J.gs(body, "doctorId");
        Map<String, Object> doctor = db.one("SELECT * FROM users WHERE id = ? "
                + "AND role = 'DOCTOR' AND is_active = 1", doctorId);
        if (doctor == null) throw new ApiError(404, "Doctor not found.");

        String appointmentId = J.gsn(body, "appointmentId");
        if (appointmentId != null) {
            Map<String, Object> appointment = db.one("SELECT * FROM appointments WHERE id = ? "
                    + "AND patient_id = ?", appointmentId, patient.id);
            if (appointment == null) throw new ApiError(404, "Appointment not found.");
        }

        double fee = DEFAULT_FEE;
        if (body != null && body.get("feeAmount") != null) {
            try {
                fee = Math.max(0, Double.parseDouble(String.valueOf(body.get("feeAmount"))));
            } catch (NumberFormatException ignored) {
                // keep the default fee
            }
        }

        String id = J.uuid();
        db.exec("INSERT INTO consultations (id, appointment_id, patient_id, doctor_id, status, "
                        + "fee_amount, fee_currency, created_at) "
                        + "VALUES (?, ?, ?, ?, 'PAYMENT_PENDING', ?, 'USD', ?)",
                id, appointmentId, patient.id, doctorId, fee, J.ts());
        notify(doctorId, "CONSULTATION_REQUEST", "Paid consultation requested",
                patient.name + " booked a paid consultation.", "/doctor/consultations");
        audit.log("CONSULTATION_CREATE", "consultation", id, "SUCCESS", J.map("fee", fee));
        return ResponseEntity.status(201).body(view(db.require(
                "SELECT * FROM consultations WHERE id = ?", id)));
    }

    /** Role-scoped list: patient and doctor see their own, admin sees all. */
    @GetMapping("/consultations/")
    public Map<String, Object> list() {
        expireStale();
        Principal user = Ctx.user();
        List<Map<String, Object>> rows;
        if (user.role.equals("PATIENT")) {
            rows = db.list("SELECT * FROM consultations WHERE patient_id = ? "
                    + "ORDER BY created_at DESC LIMIT 50", user.id);
        } else if (user.role.equals("DOCTOR")) {
            rows = db.list("SELECT * FROM consultations WHERE doctor_id = ? "
                    + "ORDER BY created_at DESC LIMIT 50", user.id);
        } else {
            rows = db.list("SELECT * FROM consultations ORDER BY created_at DESC LIMIT 100");
        }
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : rows) results.add(view(row));
        return J.map("results", results);
    }

    @GetMapping("/consultations/{id}/")
    public Map<String, Object> detail(@PathVariable String id) {
        return view(visible(id));
    }

    /**
     * ICE server configuration for the WebRTC room, served to authenticated users.
     *
     * Defaults to public Google STUN (same-network calls). For calls across the
     * internet a TURN server is required — configure it via environment
     * variables (MEDTWIN_TURN_URL / MEDTWIN_TURN_USERNAME /
     * MEDTWIN_TURN_CREDENTIAL) or run docker-compose.coturn.yml and point the
     * env at it. Credentials are injected server-side so they never sit in the
     * frontend bundle.
     */
    @GetMapping("/consultations/ice/")
    public Map<String, Object> iceConfig() {
        List<Map<String, Object>> servers = new ArrayList<>();
        String stun = System.getenv().getOrDefault("MEDTWIN_STUN_URLS",
                "stun:stun.l.google.com:19302,stun:stun1.l.google.com:19302");
        for (String url : stun.split(",")) {
            if (!url.isBlank()) servers.add(J.map("urls", url.trim()));
        }
        String turnUrl = System.getenv("MEDTWIN_TURN_URL");
        if (turnUrl != null && !turnUrl.isBlank()) {
            servers.add(J.map(
                    "urls", turnUrl,
                    "username", System.getenv().getOrDefault("MEDTWIN_TURN_USERNAME", ""),
                    "credential", System.getenv().getOrDefault("MEDTWIN_TURN_CREDENTIAL", "")));
        }
        return J.map("iceServers", servers, "turnEnabled", turnUrl != null && !turnUrl.isBlank());
    }

    /** Enter the video room. Requires the consultation to be paid (RBAC: participants only). */
    @PostMapping("/consultations/{id}/join/")
    public Map<String, Object> join(@PathVariable String id) {
        Map<String, Object> row = visible(id);
        String status = J.s(row.get("status"));
        if (status.equals("EXPIRED")) {
            throw ApiError.bad("This consultation room has expired. Book a new consultation to talk to your clinician.");
        }
        if (!status.equals("PAID") && !status.equals("WAITING_ROOM") && !status.equals("LIVE")) {
            throw ApiError.bad("Complete the payment before entering the consultation room.");
        }
        // Room validity window: reject late joins even before the sweep runs.
        Object createdAt = row.get("created_at");
        if (!status.equals("LIVE") && createdAt instanceof Timestamp ts
                && ts.before(Timestamp.valueOf(LocalDateTime.now().minusMinutes(ROOM_VALIDITY_MINUTES)))) {
            db.exec("UPDATE consultations SET status = 'EXPIRED' WHERE id = ? AND status IN ('PAID', 'WAITING_ROOM')", id);
            throw ApiError.bad("This consultation room has expired. Book a new consultation to talk to your clinician.");
        }
        String roomCode = J.s(row.get("room_code"));
        if (roomCode == null || roomCode.isBlank()) {
            roomCode = generateRoomCode();
            db.exec("UPDATE consultations SET room_code = ? WHERE id = ?", roomCode, id);
        }
        Principal user = Ctx.user();
        // First participant puts it in the waiting room; two participants make it live.
        Set<String> present = new HashSet<>(realtime.roomMembers(roomCode));
        present.add(user.id);
        String nextStatus = present.size() >= 2 ? "LIVE" : "WAITING_ROOM";
        db.exec("UPDATE consultations SET status = ?, started_at = COALESCE(started_at, ?) "
                + "WHERE id = ?", nextStatus, J.ts(), id);

        Map<String, Object> updated = db.require("SELECT * FROM consultations WHERE id = ?", id);
        String counterpart = user.role.equals("PATIENT")
                ? J.s(row.get("doctor_id")) : J.s(row.get("patient_id"));
        realtime.pushToUser(counterpart, J.map(
                "type", "consultation-update",
                "consultation", view(updated)));
        audit.log("CONSULTATION_JOIN", "consultation", id, "SUCCESS", J.map("room", roomCode));
        Map<String, Object> result = view(updated);
        result.put("room", roomCode);
        return result;
    }

    /** Doctor issues the advice / prescription note and completes the consultation. */
    @PostMapping("/consultations/{id}/prescribe/")
    public Map<String, Object> prescribe(@PathVariable String id,
                                         @RequestBody(required = false) Map<String, Object> body) {
        access.require("DOCTOR");
        Map<String, Object> row = visible(id);
        if (!Ctx.user().id.equals(J.s(row.get("doctor_id")))) {
            throw new ApiError(403, "Only the consulting doctor can issue the prescription.");
        }
        if (!List.of("PAID", "WAITING_ROOM", "LIVE").contains(J.s(row.get("status")))) {
            throw ApiError.bad("This consultation is not active.");
        }
        String note = J.gs(body, "prescriptionNote").trim();
        if (note.isEmpty()) throw ApiError.bad("Write the advice or prescription first.");
        db.exec("UPDATE consultations SET prescription_note = ?, status = 'COMPLETED', "
                        + "ended_at = ? WHERE id = ?",
                note.substring(0, Math.min(4000, note.length())), J.ts(), id);
        notify(J.s(row.get("patient_id")), "PRESCRIPTION_READY", "Prescription & advice ready",
                "Your consultation summary is ready to view.", "/patient/consultations");
        audit.log("CONSULTATION_COMPLETE", "consultation", id, "SUCCESS", null);
        return view(db.require("SELECT * FROM consultations WHERE id = ?", id));
    }

    /** Patient cancels before payment; admin can cancel at any stage. */
    @PostMapping("/consultations/{id}/cancel/")
    public Map<String, Object> cancel(@PathVariable String id) {
        Map<String, Object> row = visible(id);
        String status = J.s(row.get("status"));
        Principal user = Ctx.user();
        if (List.of("PAID", "WAITING_ROOM", "LIVE", "COMPLETED").contains(status)
                && !user.role.equals("ADMIN")) {
            throw ApiError.bad("Paid consultations cannot be cancelled — contact support for a refund.");
        }
        db.exec("UPDATE consultations SET status = 'CANCELLED', ended_at = ? WHERE id = ?", J.ts(), id);
        String counterpart = user.role.equals("PATIENT")
                ? J.s(row.get("doctor_id")) : J.s(row.get("patient_id"));
        notify(counterpart, "CONSULTATION_UPDATE", "Consultation cancelled",
                "The consultation was cancelled.", "/patient/consultations");
        return view(db.require("SELECT * FROM consultations WHERE id = ?", id));
    }

    // ------------------------------------------------------------------
    // helpers
    // ------------------------------------------------------------------
    private Map<String, Object> visible(String id) {
        Map<String, Object> row = db.one("SELECT * FROM consultations WHERE id = ?", id);
        if (row == null) throw ApiError.notFound("Not found.");
        Principal user = Ctx.user();
        boolean participant = user.id.equals(J.s(row.get("patient_id")))
                || user.id.equals(J.s(row.get("doctor_id")));
        if (!participant && !user.role.equals("ADMIN")) throw ApiError.notFound("Not found.");
        return row;
    }

    private static String generateRoomCode() {
        String alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
        StringBuilder code = new StringBuilder("MT-");
        for (int i = 0; i < 8; i++) {
            if (i == 4) code.append('-');
            code.append(alphabet.charAt(RANDOM.nextInt(alphabet.length())));
        }
        return code.toString();
    }

    private Map<String, Object> view(Map<String, Object> row) {
        Map<String, Object> doctor = db.one("SELECT id, name, avatar_color FROM users "
                + "WHERE id = ?", J.s(row.get("doctor_id")));
        Map<String, Object> patient = db.one("SELECT id, name, avatar_color FROM users "
                + "WHERE id = ?", J.s(row.get("patient_id")));
        Map<String, Object> payment = db.one("SELECT id, status, amount, currency, receipt_no, "
                + "card_last4, created_at FROM payments WHERE consultation_id = ? "
                + "ORDER BY created_at DESC LIMIT 1", J.s(row.get("id")));
        return J.map(
                "id", row.get("id"),
                "appointmentId", row.get("appointment_id"),
                "status", row.get("status"),
                "feeAmount", row.get("fee_amount"),
                "feeCurrency", row.get("fee_currency"),
                "roomCode", row.get("room_code"),
                "startedAt", J.iso(row.get("started_at")),
                "endedAt", J.iso(row.get("ended_at")),
                "prescriptionNote", row.get("prescription_note"),
                "createdAt", J.iso(row.get("created_at")),
                "doctor", doctor == null ? null : J.map(
                        "id", doctor.get("id"), "name", doctor.get("name"),
                        "avatarColor", doctor.get("avatar_color")),
                "patient", patient == null ? null : J.map(
                        "id", patient.get("id"), "name", patient.get("name"),
                        "avatarColor", patient.get("avatar_color")),
                "payment", payment == null ? null : J.map(
                        "id", payment.get("id"), "status", payment.get("status"),
                        "amount", payment.get("amount"), "currency", payment.get("currency"),
                        "receiptNo", payment.get("receipt_no"), "cardLast4", payment.get("card_last4"),
                        "createdAt", J.iso(payment.get("created_at"))));
    }

    private void notify(String userId, String type, String title, String body, String link) {
        try {
            db.exec("INSERT INTO notifications (id, user_id, type, title, body, link, "
                            + "is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                    J.uuid(), userId, type, title, body, link, J.ts());
            realtime.pushToUser(userId, J.map(
                    "type", "notification",
                    "notification", J.map("type", type, "title", title, "body", body, "link", link)));
        } catch (Exception ignored) {
            // best-effort
        }
    }
}

