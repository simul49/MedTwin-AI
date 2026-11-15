package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.web.bind.annotation.*;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * Payment ledger and checkout for paid consultations.
 *
 * The gateway is a demo card processor: cards are validated with Luhn + expiry
 * checks, transactions get a provider reference and receipt number, and cards
 * ending in 0002 simulate a decline so the failure path is testable. The
 * provider column keeps the gateway name, so a real gateway (Stripe/PayPal)
 * can replace it without touching the schema.
 */
@RestController
public class PaymentController {
    private static final SecureRandom RANDOM = new SecureRandom();

    private final Db db;
    private final Access access;
    private final Audit audit;
    private final Realtime realtime;

    public PaymentController(Db db, Access access, Audit audit, Realtime realtime) {
        this.db = db;
        this.access = access;
        this.audit = audit;
        this.realtime = realtime;
    }

    /** Role-scoped ledger: patient sees own payments, doctor sees earnings, admin sees all. */
    @GetMapping("/payments/")
    public Map<String, Object> list() {
        Principal user = Ctx.user();
        List<Map<String, Object>> rows;
        if (user.role.equals("PATIENT")) {
            rows = db.list("SELECT * FROM payments WHERE payer_id = ? "
                    + "ORDER BY created_at DESC LIMIT 50", user.id);
        } else if (user.role.equals("DOCTOR")) {
            rows = db.list("SELECT * FROM payments WHERE payee_id = ? "
                    + "ORDER BY created_at DESC LIMIT 50", user.id);
        } else {
            rows = db.list("SELECT * FROM payments ORDER BY created_at DESC LIMIT 100");
        }
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : rows) results.add(paymentView(row));
        return J.map("results", results);
    }

    /** Pay for a consultation with a card (demo gateway). */
    @PostMapping("/payments/checkout/")
    public Map<String, Object> checkout(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        String consultationId = J.gs(body, "consultationId");
        Map<String, Object> consultation = db.one("SELECT * FROM consultations WHERE id = ? "
                + "AND patient_id = ?", consultationId, patient.id);
        if (consultation == null) throw new ApiError(404, "Consultation not found.");
        if (!J.s(consultation.get("status")).equals("PAYMENT_PENDING")
                && !J.s(consultation.get("status")).equals("SCHEDULED")) {
            throw ApiError.bad("This consultation has already been paid or cancelled.");
        }

        String cardNumber = J.gs(body, "cardNumber").replaceAll("[\\s-]", "");
        String cardName = J.gs(body, "cardName").trim();
        String expiry = J.gs(body, "expiry").trim();       // MM/YY
        String cvc = J.gs(body, "cvc").trim();

        if (cardName.isEmpty()) throw ApiError.bad("Enter the cardholder name.");
        if (!cardNumber.matches("\\d{13,19}") || !luhnValid(cardNumber)) {
            throw ApiError.bad("That card number is not valid.");
        }
        if (!expiry.matches("(0[1-9]|1[0-2])/\\d{2}")) {
            throw ApiError.bad("Expiry must be in MM/YY format.");
        }
        String[] parts = expiry.split("/");
        int month = Integer.parseInt(parts[0]);
        int year = 2000 + Integer.parseInt(parts[1]);
        LocalDateTime now = LocalDateTime.now();
        if (year < now.getYear() || (year == now.getYear() && month < now.getMonthValue())) {
            throw ApiError.bad("That card has expired.");
        }
        if (!cvc.matches("\\d{3,4}")) throw ApiError.bad("Enter the 3 or 4 digit security code.");

        String last4 = cardNumber.substring(cardNumber.length() - 4);
        String paymentId = J.uuid();
        double amount = Double.parseDouble(String.valueOf(consultation.get("fee_amount")));

        // Demo gateway: 0002-suffixed cards decline so the failure path is testable.
        boolean declined = last4.equals("0002");
        String status = declined ? "FAILED" : "PAID";
        String providerRef = declined ? null : "demo_" + J.uuid().substring(0, 12);
        String receiptNo = declined ? null : "RCP-" + now.format(DateTimeFormatter.BASIC_ISO_DATE)
                + "-" + (1000 + RANDOM.nextInt(9000));

        db.exec("INSERT INTO payments (id, consultation_id, appointment_id, payer_id, payee_id, "
                        + "amount, currency, purpose, method, provider, provider_ref, card_last4, "
                        + "status, receipt_no, created_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, 'USD', 'CONSULTATION', 'CARD', 'DEMO_GATEWAY', "
                        + "?, ?, ?, ?, ?)",
                paymentId, consultationId, consultation.get("appointment_id"), patient.id,
                consultation.get("doctor_id"), amount, providerRef, last4, status, receiptNo, J.ts());

        if (declined) {
            audit.log("PAYMENT_FAILED", "payment", paymentId, "DECLINED", J.map("last4", last4));
            throw new ApiError(402, "Card declined by the gateway (test card). No charge was made.");
        }

        db.exec("UPDATE consultations SET status = 'PAID' WHERE id = ?", consultationId);
        Map<String, Object> updated = db.require(
                "SELECT * FROM consultations WHERE id = ?", consultationId);
        notify(J.s(consultation.get("doctor_id")), "PAYMENT_RECEIVED", "Consultation paid",
                patient.name + " paid for the consultation. Enter the room when ready.",
                "/doctor/consultations");
        audit.log("PAYMENT_SUCCESS", "payment", paymentId, "SUCCESS",
                J.map("amount", amount, "receipt", receiptNo));

        Map<String, Object> result = paymentView(db.require(
                "SELECT * FROM payments WHERE id = ?", paymentId));
        result.put("consultation", consultationView(updated));
        return result;
    }

    /** Printable receipt. */
    @GetMapping("/payments/{id}/receipt/")
    public Map<String, Object> receipt(@PathVariable String id) {
        Map<String, Object> row = db.one("SELECT * FROM payments WHERE id = ?", id);
        if (row == null) throw ApiError.notFound("Not found.");
        Principal user = Ctx.user();
        boolean allowed = user.id.equals(J.s(row.get("payer_id")))
                || user.id.equals(J.s(row.get("payee_id"))) || user.role.equals("ADMIN");
        if (!allowed) throw ApiError.notFound("Not found.");
        Map<String, Object> result = paymentView(row);
        Map<String, Object> consultation = db.one(
                "SELECT id, status, prescription_note, created_at FROM consultations WHERE id = ?",
                J.s(row.get("consultation_id")));
        result.put("consultation", consultation);
        return result;
    }

    private static boolean luhnValid(String number) {
        int sum = 0;
        boolean alternate = false;
        for (int i = number.length() - 1; i >= 0; i--) {
            int digit = number.charAt(i) - '0';
            if (alternate) {
                digit *= 2;
                if (digit > 9) digit -= 9;
            }
            sum += digit;
            alternate = !alternate;
        }
        return sum % 10 == 0;
    }

    private Map<String, Object> paymentView(Map<String, Object> row) {
        Map<String, Object> payer = db.one("SELECT id, name FROM users WHERE id = ?",
                J.s(row.get("payer_id")));
        Map<String, Object> payee = db.one("SELECT id, name, avatar_color FROM users WHERE id = ?",
                J.s(row.get("payee_id")));
        return J.map(
                "id", row.get("id"),
                "consultationId", row.get("consultation_id"),
                "appointmentId", row.get("appointment_id"),
                "amount", row.get("amount"),
                "currency", row.get("currency"),
                "purpose", row.get("purpose"),
                "method", row.get("method"),
                "provider", row.get("provider"),
                "providerRef", row.get("provider_ref"),
                "cardLast4", row.get("card_last4"),
                "status", row.get("status"),
                "receiptNo", row.get("receipt_no"),
                "createdAt", J.iso(row.get("created_at")),
                "payerName", payer == null ? null : payer.get("name"),
                "payee", payee == null ? null : J.map(
                        "id", payee.get("id"), "name", payee.get("name"),
                        "avatarColor", payee.get("avatar_color")));
    }

    private Map<String, Object> consultationView(Map<String, Object> row) {
        Map<String, Object> doctor = db.one("SELECT id, name, avatar_color FROM users "
                + "WHERE id = ?", J.s(row.get("doctor_id")));
        return J.map(
                "id", row.get("id"),
                "status", row.get("status"),
                "feeAmount", row.get("fee_amount"),
                "feeCurrency", row.get("fee_currency"),
                "roomCode", row.get("room_code"),
                "doctor", doctor == null ? null : J.map(
                        "id", doctor.get("id"), "name", doctor.get("name"),
                        "avatarColor", doctor.get("avatar_color")),
                "createdAt", J.iso(row.get("created_at")));
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
