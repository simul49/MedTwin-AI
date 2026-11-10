package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/** Patient-to-doctor consent workflow. Every change is audited and notified. */
@RestController
public class ConsentController {
    private final Db db;
    private final Access access;
    private final Audit audit;

    public ConsentController(Db db, Access access, Audit audit) {
        this.db = db;
        this.access = access;
        this.audit = audit;
    }

    @GetMapping("/consent/grants/")
    public Map<String, Object> list() {
        Principal user = Ctx.user();
        List<Map<String, Object>> rows;
        if (user.role.equals("PATIENT")) {
            rows = db.list("SELECT * FROM consent_grants WHERE patient_id = ? "
                    + "ORDER BY created_at DESC", user.id);
        } else if (user.role.equals("DOCTOR")) {
            rows = db.list("SELECT * FROM consent_grants WHERE doctor_id = ? "
                    + "ORDER BY created_at DESC", user.id);
        } else {
            rows = db.list("SELECT * FROM consent_grants ORDER BY created_at DESC LIMIT 200");
        }
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : rows) results.add(Views.grant(db, row));
        return J.map("results", results, "scopeOptions", Access.SCOPE_OPTIONS);
    }

    @PostMapping("/consent/requests/")
    public ResponseEntity<Object> request(@RequestBody(required = false) Map<String, Object> body) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        String patientId = J.gs(body, "patientId");
        Map<String, Object> patient = db.one(
                "SELECT * FROM users WHERE id = ? AND role = 'PATIENT'", patientId);
        if (patient == null) throw new ApiError(404, "Patient not found.");

        Map<String, Object> existing = db.one("SELECT * FROM consent_grants "
                + "WHERE doctor_id = ? AND patient_id = ? AND status IN ('PENDING', 'ACTIVE')",
                doctor.id, patientId);
        if (existing != null) {
            ApiError error = ApiError.conflict("A request or grant already exists for this patient.");
            error.body.put("grant", Views.grant(db, existing));
            throw error;
        }

        List<String> scope = access.parseScope(J.g(body, "scope"));
        String id = createGrant(patientId, doctor.id, scope, J.gs(body, "purpose").trim(),
                "PENDING", J.gi(body, "durationDays", 90));
        notify(patientId, "CONSENT_REQUEST", "A doctor has requested access",
                doctor.name + " requested access to: " + String.join(", ", scope) + ".", "/consent");
        audit.log("CONSENT_REQUEST", "consent_grant", id, "SUCCESS",
                J.map("patientId", patientId, "scope", scope));
        return ResponseEntity.status(201).body(
                Views.grant(db, db.require("SELECT * FROM consent_grants WHERE id = ?", id)));
    }

    @PostMapping("/consent/grants/new/")
    public ResponseEntity<Object> grantDirect(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        String doctorId = J.gs(body, "doctorId");
        Map<String, Object> doctor = db.one("SELECT * FROM users WHERE id = ? "
                + "AND role = 'DOCTOR' AND is_active = 1", doctorId);
        if (doctor == null) throw new ApiError(404, "Doctor not found.");
        List<String> scope = access.parseScope(J.g(body, "scope"));
        String id = createGrant(patient.id, doctorId, scope, J.gs(body, "purpose").trim(),
                "ACTIVE", J.gi(body, "durationDays", 90));
        notify(doctorId, "CONSENT_GRANTED", "A patient granted you access",
                patient.name + " granted access to: " + String.join(", ", scope) + ".", "/doctor");
        audit.log("CONSENT_GRANT", "consent_grant", id, "SUCCESS",
                J.map("doctorId", doctorId, "scope", scope));
        return ResponseEntity.status(201).body(
                Views.grant(db, db.require("SELECT * FROM consent_grants WHERE id = ?", id)));
    }

    @PostMapping("/consent/grants/{id}/decision/")
    public Map<String, Object> decide(@PathVariable String id,
                                      @RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        Map<String, Object> grant = db.one("SELECT * FROM consent_grants WHERE id = ? "
                + "AND patient_id = ? AND status = 'PENDING'", id, patient.id);
        if (grant == null) throw new ApiError(404, "No pending request found.");
        String decision = J.gs(body, "decision").toUpperCase();
        if (!Set.of("GRANT", "REJECT").contains(decision)) {
            throw ApiError.bad("Decision must be GRANT or REJECT.");
        }
        String doctorId = J.s(grant.get("doctor_id"));
        List<String> scope = J.strings(grant.get("scope"));
        if (decision.equals("GRANT")) {
            if (J.g(body, "scope") != null) scope = access.parseScope(J.g(body, "scope"));
            db.exec("UPDATE consent_grants SET status = 'ACTIVE', granted_at = ?, scope = ?, "
                            + "expires_at = ?, updated_at = ? WHERE id = ?",
                    J.ts(), J.toJson(scope),
                    J.plusDays(J.gi(body, "durationDays", 90)), J.ts(), id);
            notify(doctorId, "CONSENT_GRANTED", "Access request approved",
                    patient.name + " approved your access request.", "/doctor");
        } else {
            db.exec("UPDATE consent_grants SET status = 'REJECTED', updated_at = ? WHERE id = ?",
                    J.ts(), id);
            notify(doctorId, "CONSENT_REJECTED", "Access request declined",
                    patient.name + " declined your access request.", "/doctor");
        }
        audit.log("CONSENT_DECISION", "consent_grant", id, "SUCCESS",
                J.map("decision", decision, "scope", scope));
        return Views.grant(db, db.require("SELECT * FROM consent_grants WHERE id = ?", id));
    }

    @PostMapping("/consent/grants/{id}/revoke/")
    public Map<String, Object> revoke(@PathVariable String id) {
        access.require("PATIENT");
        Principal patient = Ctx.user();
        Map<String, Object> grant = db.one("SELECT * FROM consent_grants WHERE id = ? "
                + "AND patient_id = ? AND status = 'ACTIVE'", id, patient.id);
        if (grant == null) throw new ApiError(404, "No active grant found.");
        db.exec("UPDATE consent_grants SET status = 'REVOKED', revoked_at = ?, "
                + "updated_at = ? WHERE id = ?", J.ts(), J.ts(), id);
        notify(J.s(grant.get("doctor_id")), "CONSENT_REVOKED", "Access was revoked",
                patient.name + " revoked your access. Future requests will be blocked.", "/doctor");
        audit.log("CONSENT_REVOKE", "consent_grant", id, "SUCCESS",
                J.map("doctorId", J.s(grant.get("doctor_id"))));
        return Views.grant(db, db.require("SELECT * FROM consent_grants WHERE id = ?", id));
    }

    private String createGrant(String patientId, String doctorId, List<String> scope,
                               String purpose, String status, int durationDays) {
        String id = J.uuid();
        db.exec("INSERT INTO consent_grants (id, patient_id, doctor_id, scope, purpose, status, "
                        + "granted_at, expires_at, created_at, updated_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                id, patientId, doctorId, J.toJson(scope),
                purpose.isEmpty() ? null : purpose.substring(0, Math.min(255, purpose.length())),
                status, status.equals("ACTIVE") ? J.ts() : null,
                J.plusDays(durationDays), J.ts(), J.ts());
        return id;
    }

    private void notify(String userId, String type, String title, String body, String link) {
        try {
            db.exec("INSERT INTO notifications (id, user_id, type, title, body, link, "
                            + "is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, 0, ?)",
                    J.uuid(), userId, type, title, body, link, J.ts());
        } catch (Exception ignored) {
            // notifications are best-effort
        }
    }
}
