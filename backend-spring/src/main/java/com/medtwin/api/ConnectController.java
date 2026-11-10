package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.*;

/** Secure messaging, appointments and notifications. */
@RestController
public class ConnectController {
    private static final Set<String> APPOINTMENT_STATUSES = Set.of(
            "REQUESTED", "CONFIRMED", "DECLINED", "COMPLETED", "CANCELLED");

    private final Db db;
    private final Access access;
    private final Audit audit;

    public ConnectController(Db db, Access access, Audit audit) {
        this.db = db;
        this.access = access;
        this.audit = audit;
    }

    @GetMapping("/conversations/")
    public Map<String, Object> conversations() {
        Principal user = Ctx.user();
        List<Map<String, Object>> rows;
        if (user.role.equals("PATIENT")) {
            rows = db.list("SELECT * FROM conversations WHERE patient_id = ? "
                    + "AND channel <> 'PATIENT_AI' ORDER BY updated_at DESC", user.id);
        } else if (user.role.equals("DOCTOR")) {
            rows = db.list("SELECT * FROM conversations WHERE doctor_id = ? "
                    + "AND channel <> 'PATIENT_AI' ORDER BY updated_at DESC", user.id);
        } else {
            rows = List.of();
        }
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : rows) results.add(Views.conversation(db, row, user));
        return J.map("results", results);
    }

    @PostMapping("/conversations/")
    public ResponseEntity<Object> startConversation(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        String doctorId = J.gs(body, "doctorId");
        Map<String, Object> doctor = db.one("SELECT * FROM users WHERE id = ? "
                + "AND role = 'DOCTOR' AND is_active = 1", doctorId);
        if (doctor == null) throw new ApiError(404, "Doctor not found.");
        if (!access.grantIsLive(access.activeGrant(doctorId, patient.id))) {
            audit.log("ACCESS_DENIED", "conversation", "", "DENIED",
                    J.map("reason", "no_active_grant", "doctorId", doctorId));
            throw new ApiError(403, "Grant access to this doctor before starting a conversation.");
        }
        Map<String, Object> existing = db.one("SELECT * FROM conversations WHERE patient_id = ? "
                + "AND doctor_id = ? AND channel = 'PATIENT_DOCTOR'", patient.id, doctorId);
        if (existing == null) {
            db.exec("INSERT INTO conversations (id, patient_id, doctor_id, title, channel, "
                            + "created_at, updated_at) VALUES (?, ?, ?, ?, 'PATIENT_DOCTOR', ?, ?)",
                    J.uuid(), patient.id, doctorId, J.s(doctor.get("name")), J.ts(), J.ts());
            existing = db.one("SELECT * FROM conversations WHERE patient_id = ? "
                    + "AND doctor_id = ? AND channel = 'PATIENT_DOCTOR'", patient.id, doctorId);
        }
        return ResponseEntity.status(201).body(Views.conversation(db, existing, patient));
    }

    @GetMapping("/conversations/{id}/")
    public Map<String, Object> conversation(@PathVariable String id) {
        Map<String, Object> row = visibleConversation(id);
        List<Map<String, Object>> messages = new ArrayList<>();
        for (Map<String, Object> message : db.list("SELECT * FROM messages "
                + "WHERE conversation_id = ? ORDER BY created_at ASC LIMIT 300", id)) {
            messages.add(Views.message(db, message));
        }
        db.exec("UPDATE messages SET read_at = ? WHERE conversation_id = ? "
                        + "AND read_at IS NULL AND (sender_id IS NULL OR sender_id <> ?)",
                J.ts(), id, Ctx.user().id);
        return J.map("id", id, "title", J.sn(row.get("title")), "messages", messages);
    }

    @PostMapping("/conversations/{id}/")
    public ResponseEntity<Object> sendMessage(@PathVariable String id,
                                              @RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> conversation = visibleConversation(id);
        String text = J.gs(body, "body").trim();
        if (text.isEmpty()) throw ApiError.bad("Write a message first.");
        Principal user = Ctx.user();
        if (user.role.equals("DOCTOR") && !access.grantIsLive(
                access.activeGrant(user.id, J.s(conversation.get("patient_id"))))) {
            throw new ApiError(403, "Your access to this patient is no longer active.");
        }
        String messageId = J.uuid();
        db.exec("INSERT INTO messages (id, conversation_id, sender_id, role, body, "
                        + "created_at) VALUES (?, ?, ?, ?, ?, ?)",
                messageId, id, user.id, user.role.equals("DOCTOR") ? "DOCTOR" : "USER",
                text.substring(0, Math.min(4000, text.length())), J.ts());
        db.exec("UPDATE conversations SET updated_at = ? WHERE id = ?", J.ts(), id);
        return ResponseEntity.status(201).body(Views.message(db,
                db.require("SELECT * FROM messages WHERE id = ?", messageId)));
    }

    private Map<String, Object> visibleConversation(String id) {
        Map<String, Object> row = db.one("SELECT * FROM conversations WHERE id = ?", id);
        if (row == null) throw ApiError.notFound("Not found.");
        Principal user = Ctx.user();
        if (user.role.equals("PATIENT") && !user.id.equals(J.s(row.get("patient_id")))) {
            throw ApiError.notFound("Not found.");
        }
        if (user.role.equals("DOCTOR") && !user.id.equals(J.s(row.get("doctor_id")))) {
            throw ApiError.notFound("Not found.");
        }
        return row;
    }

    @GetMapping("/appointments/")
    public Map<String, Object> appointments() {
        Principal user = Ctx.user();
        List<Map<String, Object>> rows;
        if (user.role.equals("PATIENT")) {
            rows = db.list("SELECT * FROM appointments WHERE patient_id = ? "
                    + "ORDER BY scheduled_at DESC LIMIT 50", user.id);
        } else if (user.role.equals("DOCTOR")) {
            rows = db.list("SELECT * FROM appointments WHERE doctor_id = ? "
                    + "ORDER BY scheduled_at DESC LIMIT 50", user.id);
        } else {
            rows = List.of();
        }
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : rows) results.add(Views.appointment(db, row));
        return J.map("results", results);
    }

    @PostMapping("/appointments/")
    public ResponseEntity<Object> createAppointment(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        String doctorId = J.gs(body, "doctorId");
        Map<String, Object> doctor = db.one("SELECT * FROM users WHERE id = ? "
                + "AND role = 'DOCTOR' AND is_active = 1", doctorId);
        if (doctor == null) throw new ApiError(404, "Doctor not found.");
        if (J.gs(body, "scheduledAt").isBlank()) throw ApiError.bad("Choose a date and time.");
        String id = J.uuid();
        db.exec("INSERT INTO appointments (id, patient_id, doctor_id, scheduled_at, "
                        + "duration_min, timezone, reason, status, created_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, 'REQUESTED', ?)",
                id, patient.id, doctorId, parseDateTime(J.gs(body, "scheduledAt")),
                J.gi(body, "durationMin", 30),
                J.gs(body, "timezone").isEmpty() ? "UTC" : J.gs(body, "timezone"),
                blankToNull(J.gs(body, "reason").trim()), J.ts());
        notify(doctorId, "APPOINTMENT_REQUEST", "New appointment request",
                patient.name + " requested an appointment.", "/doctor/appointments");
        audit.log("APPOINTMENT_CREATE", "appointment", id, "SUCCESS", null);
        return ResponseEntity.status(201).body(Views.appointment(db,
                db.require("SELECT * FROM appointments WHERE id = ?", id)));
    }

    @PatchMapping("/appointments/{id}/")
    public Map<String, Object> updateAppointment(@PathVariable String id,
                                                 @RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> row = visibleAppointment(id);
        String status = J.gs(body, "status").toUpperCase();
        if (!APPOINTMENT_STATUSES.contains(status)) throw ApiError.bad("Unknown appointment status.");
        List<String> sets = new ArrayList<>(List.of("status = ?"));
        List<Object> args = new ArrayList<>(List.of(status));
        if (body != null && body.containsKey("notes")) {
            sets.add("notes = ?");
            args.add(blankToNull(J.gs(body, "notes")));
        }
        if (body != null && !J.gs(body, "scheduledAt").isBlank()) {
            sets.add("scheduled_at = ?");
            args.add(parseDateTime(J.gs(body, "scheduledAt")));
        }
        args.add(id);
        db.exec("UPDATE appointments SET " + String.join(", ", sets) + " WHERE id = ?",
                args.toArray());
        String counterpart = Ctx.user().role.equals("PATIENT")
                ? J.s(row.get("doctor_id")) : J.s(row.get("patient_id"));
        if (!counterpart.isEmpty()) {
            notify(counterpart, "APPOINTMENT_UPDATE", "Appointment " + status.toLowerCase(),
                    "Appointment is now " + status.toLowerCase() + ".", "/appointments");
        }
        audit.log("APPOINTMENT_UPDATE", "appointment", id, "SUCCESS", J.map("status", status));
        return Views.appointment(db, db.require("SELECT * FROM appointments WHERE id = ?", id));
    }

    private Map<String, Object> visibleAppointment(String id) {
        Map<String, Object> row = db.one("SELECT * FROM appointments WHERE id = ?", id);
        if (row == null) throw ApiError.notFound("Not found.");
        Principal user = Ctx.user();
        if (user.role.equals("PATIENT") && !user.id.equals(J.s(row.get("patient_id")))) {
            throw ApiError.notFound("Not found.");
        }
        if (user.role.equals("DOCTOR") && !user.id.equals(J.s(row.get("doctor_id")))) {
            throw ApiError.notFound("Not found.");
        }
        return row;
    }

    @GetMapping("/notifications/")
    public Map<String, Object> notifications() {
        String userId = Ctx.user().id;
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM notifications WHERE user_id = ? "
                + "ORDER BY created_at DESC LIMIT 50", userId)) {
            results.add(Views.notification(row));
        }
        return J.map(
                "unread", db.count("SELECT COUNT(*) FROM notifications WHERE user_id = ? "
                        + "AND is_read = 0", userId),
                "results", results);
    }

    @PostMapping("/notifications/read-all/")
    public Map<String, Object> readAll() {
        db.exec("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                Ctx.user().id);
        return J.map("ok", true);
    }

    @PostMapping("/notifications/{id}/read/")
    public Map<String, Object> readOne(@PathVariable String id) {
        int updated = db.exec("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                id, Ctx.user().id);
        if (updated == 0) throw ApiError.notFound("Not found.");
        return J.map("ok", true);
    }

    private void notify(String userId, String type, String title, String body, String link) {
        try {
            db.exec("INSERT INTO notifications (id, user_id, type, title, body, link, "
                            + "is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                    J.uuid(), userId, type, title, body, link, J.ts());
        } catch (Exception ignored) {
            // best-effort
        }
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private static Timestamp parseDateTime(String value) {
        String text = value.trim().replace(' ', 'T');
        try {
            return Timestamp.valueOf(OffsetDateTime.parse(text).toLocalDateTime());
        } catch (Exception ignored) {
            // try a naive local datetime
        }
        try {
            return Timestamp.valueOf(LocalDateTime.parse(text));
        } catch (Exception ignored) {
            // try minute precision
        }
        if (text.length() >= 16) {
            try {
                return Timestamp.valueOf(LocalDateTime.parse(text.substring(0, 16) + ":00"));
            } catch (Exception ignored) {
                // fall through
            }
        }
        return J.ts();
    }
}
