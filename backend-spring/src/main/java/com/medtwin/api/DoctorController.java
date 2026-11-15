package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/** Doctor workspace. Every lookup is gated by a live, in-scope consent grant. */
@RestController
public class DoctorController {
    private final Db db;
    private final Access access;
    private final Audit audit;
    private final Realtime realtime;

    public DoctorController(Db db, Access access, Audit audit, Realtime realtime) {
        this.db = db;
        this.access = access;
        this.audit = audit;
        this.realtime = realtime;
    }

    /**
     * Clinician-recorded observation (real-time data entry). Requires an active
     * consent whose scope includes lab results; the patient is notified over
     * WebSocket so their dashboard updates the moment the value lands.
     */
    @PostMapping("/doctor/patients/{patientId}/observations/")
    public ResponseEntity<Object> addObservation(@PathVariable String patientId,
                                                 @RequestBody(required = false) Map<String, Object> body) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        Map<String, Object> patient = access.resolvePatient(doctor, patientId);
        String pid = J.s(patient.get("id"));
        List<String> scope = access.scope(doctor, pid);
        if (!scope.contains("all") && !access.has(scope, "lab_results")) {
            throw ApiError.forbidden();
        }

        String label = J.gs(body, "label").trim();
        if (label.isEmpty()) throw ApiError.bad("Label the measurement.");
        String valueRaw = J.gs(body, "value").trim();
        if (valueRaw.isEmpty()) throw ApiError.bad("Provide the measured value.");
        Double numeric;
        try {
            numeric = Double.valueOf(valueRaw);
        } catch (NumberFormatException e) {
            throw ApiError.bad("Value must be numeric.");
        }
        String flag = J.gs(body, "flag").trim().toUpperCase();
        if (!Set.of("NORMAL", "LOW", "HIGH", "CRITICAL").contains(flag)) {
            throw ApiError.bad("Unknown flag.");
        }
        String referenceRange = J.gs(body, "reference_range").trim();

        String id = J.uuid();
        db.exec("INSERT INTO observations (id, patient_id, label, value_numeric, value_text, unit, "
                        + "reference_range, flag, observed_at, source_type, created_at) "
                        + "VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, 'CLINICIAN', ?)",
                id, pid, label, numeric,
                J.gs(body, "unit").trim().isEmpty() ? null : J.gs(body, "unit").trim(),
                referenceRange.isEmpty() ? null : referenceRange,
                flag, J.ts(), J.ts());
        audit.log("CLINICIAN_OBSERVATION_CREATE", "observation", id, "SUCCESS",
                J.map("patientId", pid, "label", label));

        // Real-time: the patient's dashboard reloads itself on this notification.
        try {
            realtime.pushToUser(pid, J.map(
                    "type", "notification",
                    "notification", J.map(
                            "type", "OBSERVATION_UPDATE",
                            "title", "New clinician reading",
                            "body", label + " " + valueRaw
                                    + (J.gs(body, "unit").trim().isEmpty() ? "" : " " + J.gs(body, "unit").trim())
                                    + " was recorded by your clinician.",
                            "link", "/patient")));
        } catch (Exception ignored) {
            // best-effort
        }

        return ResponseEntity.status(201).body(
                Views.observation(db.require("SELECT * FROM observations WHERE id = ?", id)));
    }

    @GetMapping("/doctor/authorized-patients/")
    public Map<String, Object> authorizedPatients() {
        access.require("DOCTOR");
        String doctorId = Ctx.user().id;
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> patient : db.list(
                "SELECT DISTINCT u.* FROM users u JOIN consent_grants g ON g.patient_id = u.id "
                        + "WHERE g.doctor_id = ? AND g.status = 'ACTIVE' AND u.role = 'PATIENT' "
                        + "AND (g.expires_at IS NULL OR g.expires_at > ?) "
                        + "ORDER BY u.created_at DESC", doctorId, J.ts())) {
            String pid = J.s(patient.get("id"));
            Map<String, Object> grant = db.one("SELECT * FROM consent_grants "
                    + "WHERE doctor_id = ? AND patient_id = ? AND status = 'ACTIVE' "
                    + "ORDER BY created_at DESC LIMIT 1", doctorId, pid);
            Map<String, Object> profile = db.one(
                    "SELECT * FROM patient_profiles WHERE user_id = ?", pid);
            Map<String, Object> last = db.one("SELECT occurred_at FROM timeline_events "
                    + "WHERE patient_id = ? ORDER BY occurred_at DESC LIMIT 1", pid);
            Principal identity = new Principal(patient);
            results.add(J.map(
                    "id", pid,
                    "name", identity.name,
                    "email", identity.email,
                    "initials", identity.initials,
                    "avatarColor", identity.avatarColor,
                    "age", profile == null ? null : Views.patientProfile(profile).get("age"),
                    "gender", profile == null ? "UNDISCLOSED" : J.s(profile.get("gender")),
                    "scope", grant == null ? List.of() : J.strings(grant.get("scope")),
                    "expiresAt", grant == null ? null : J.iso(grant.get("expires_at")),
                    "openFlags", db.count("SELECT COUNT(*) FROM observations WHERE patient_id = ? "
                            + "AND flag NOT IN ('NORMAL', 'UNKNOWN')", pid),
                    "recordCount", db.count("SELECT COUNT(*) FROM health_records WHERE patient_id = ?", pid),
                    "lastActivity", last == null ? null : J.iso(last.get("occurred_at"))));
        }
        return J.map("results", results);
    }

    @GetMapping("/doctor/patients/{patientId}/summary/")
    public Map<String, Object> summary(@PathVariable String patientId) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        Map<String, Object> patient = access.resolvePatient(doctor, patientId);
        String pid = J.s(patient.get("id"));
        List<String> scope = access.scope(doctor, pid);
        List<String> categories = access.categories(scope);

        List<Map<String, Object>> records = new ArrayList<>();
        if (scope.contains("all")) {
            for (Map<String, Object> row : db.list("SELECT * FROM health_records "
                    + "WHERE patient_id = ? ORDER BY recorded_at DESC, created_at DESC LIMIT 50", pid)) {
                records.add(Views.record(row));
            }
        } else if (!categories.isEmpty()) {
            String marks = String.join(",", Collections.nCopies(categories.size(), "?"));
            List<Object> args = new ArrayList<>(List.of(pid));
            args.addAll(categories);
            for (Map<String, Object> row : db.list("SELECT * FROM health_records "
                    + "WHERE patient_id = ? AND category IN (" + marks + ") "
                    + "ORDER BY recorded_at DESC, created_at DESC LIMIT 50", args.toArray())) {
                records.add(Views.record(row));
            }
        }

        Map<String, Object> profile = db.one("SELECT * FROM patient_profiles WHERE user_id = ?", pid);
        Map<String, Object> draft = db.one("SELECT * FROM health_records WHERE patient_id = ? "
                + "AND source_type = 'AI_GENERATED' AND category = 'NOTE' "
                + "ORDER BY created_at DESC LIMIT 1", pid);
        Principal identity = new Principal(patient);

        audit.log("PATIENT_VIEW", "patient", pid, "SUCCESS", J.map("scope", scope));
        return J.map(
                "patient", J.map("id", pid, "name", identity.name,
                        "email", identity.email, "initials", identity.initials),
                "scope", scope,
                "profile", access.has(scope, "profile") && profile != null
                        ? Views.patientProfile(profile) : J.map(),
                "records", records,
                "observations", access.has(scope, "lab_results")
                        ? observations(pid, 20) : List.of(),
                "allergies", access.has(scope, "allergies") ? allergies(pid) : List.of(),
                "medications", access.has(scope, "medications") ? medications(pid) : List.of(),
                "documents", access.has(scope, "documents") ? documents(pid) : List.of(),
                "timeline", access.has(scope, "timeline") ? timeline(pid, 30) : List.of(),
                "draftSummary", draft == null ? null : Views.record(draft));
    }

    @PostMapping("/doctor/patients/{patientId}/summary/")
    public ResponseEntity<Object> createDraftSummary(@PathVariable String patientId) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        Map<String, Object> patient = access.resolvePatient(doctor, patientId);
        String pid = J.s(patient.get("id"));
        List<String> scope = access.scope(doctor, pid);
        List<String> categories = access.categories(scope);

        List<String> lines = new ArrayList<>();
        lines.add("AI-generated draft summary — NOT clinician-verified.");
        lines.add("");
        lines.add("Patient: " + J.s(patient.get("name")));
        List<Map<String, Object>> records = scopedRecords(pid, scope, categories, 20);
        if (!records.isEmpty()) {
            lines.add("");
            lines.add("Conditions and history:");
            for (Map<String, Object> row : records) {
                lines.add("- " + J.s(row.get("title")) + " ("
                        + J.s(row.get("verification_status")).toLowerCase().replace('_', ' ') + ")");
            }
        }
        if (access.has(scope, "medications")) {
            List<Map<String, Object>> meds = db.list("SELECT * FROM medications "
                    + "WHERE patient_id = ? AND status = 'ACTIVE' ORDER BY created_at DESC LIMIT 10", pid);
            if (!meds.isEmpty()) {
                lines.add("");
                lines.add("Active medications:");
                for (Map<String, Object> row : meds) {
                    lines.add(("- " + J.s(row.get("name")) + " " + J.s(row.get("dose")) + " "
                            + J.s(row.get("frequency"))).trim());
                }
            }
        }
        if (access.has(scope, "allergies")) {
            List<Map<String, Object>> items = db.list("SELECT * FROM allergies "
                    + "WHERE patient_id = ? ORDER BY created_at DESC LIMIT 10", pid);
            if (!items.isEmpty()) {
                lines.add("");
                lines.add("Allergies:");
                for (Map<String, Object> row : items) {
                    lines.add("- " + J.s(row.get("substance")) + " ("
                            + J.s(row.get("severity")).toLowerCase() + ")");
                }
            }
        }
        if (access.has(scope, "lab_results")) {
            List<Map<String, Object>> items = db.list("SELECT * FROM observations "
                    + "WHERE patient_id = ? ORDER BY observed_at DESC LIMIT 10", pid);
            if (!items.isEmpty()) {
                lines.add("");
                lines.add("Recent results:");
                for (Map<String, Object> row : items) {
                    lines.add("- " + J.s(row.get("label")) + ": "
                            + J.s(Views.observation(row).get("displayValue")) + " ("
                            + J.s(row.get("flag")).toLowerCase() + ")");
                }
            }
        }
        lines.add("");
        lines.add("Sources: patient Digital Twin records only. Requires clinician review before use.");
        String text = String.join("\n", lines);
        if (text.length() > 4000) text = text.substring(0, 4000);

        Map<String, Object> existing = db.one("SELECT * FROM health_records WHERE patient_id = ? "
                + "AND source_type = 'AI_GENERATED' AND verification_status = 'UNVERIFIED' "
                + "ORDER BY created_at DESC LIMIT 1", pid);
        boolean created = existing == null;
        String id;
        if (created) {
            id = J.uuid();
            db.exec("INSERT INTO health_records (id, patient_id, category, title, summary, "
                            + "source_type, verification_status, author_id, recorded_at, "
                            + "created_at, updated_at) VALUES (?, ?, 'NOTE', ?, ?, "
                            + "'AI_GENERATED', 'UNVERIFIED', ?, ?, ?, ?)",
                    id, pid, "AI draft summary (requires review)", text,
                    doctor.id, J.ts(), J.ts(), J.ts());
        } else {
            id = J.s(existing.get("id"));
            db.exec("UPDATE health_records SET summary = ?, recorded_at = ? WHERE id = ?",
                    text, J.ts(), id);
        }
        audit.log(created ? "SUMMARY_DRAFT_CREATE" : "SUMMARY_DRAFT_UPDATE",
                "health_record", id, "SUCCESS", J.map("patientId", pid));
        return ResponseEntity.status(created ? 201 : 200).body(
                Views.record(db.require("SELECT * FROM health_records WHERE id = ?", id)));
    }

    @GetMapping("/doctor/patients/{patientId}/records/")
    public Map<String, Object> doctorRecords(@PathVariable String patientId) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        access.resolvePatient(doctor, patientId);
        List<String> scope = access.scope(doctor, patientId);
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : scopedRecords(patientId, scope,
                access.categories(scope), 100)) {
            results.add(Views.record(row));
        }
        return J.map("results", results);
    }

    @GetMapping("/doctor/patients/{patientId}/documents/")
    public Map<String, Object> doctorDocuments(@PathVariable String patientId) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        access.resolvePatient(doctor, patientId);
        if (!access.has(access.scope(doctor, patientId), "documents")) {
            return J.map("results", List.of());
        }
        return J.map("results", documents(patientId));
    }

    @GetMapping("/doctor/patients/{patientId}/timeline/")
    public Map<String, Object> doctorTimeline(@PathVariable String patientId) {
        access.require("DOCTOR");
        Principal doctor = Ctx.user();
        access.resolvePatient(doctor, patientId);
        if (!access.has(access.scope(doctor, patientId), "timeline")) {
            return J.map("results", List.of());
        }
        return J.map("results", timeline(patientId, 100));
    }

    private List<Map<String, Object>> scopedRecords(String pid, List<String> scope,
                                                    List<String> categories, int limit) {
        if (scope.contains("all") || categories.isEmpty()) {
            return db.list("SELECT * FROM health_records WHERE patient_id = ? "
                    + "ORDER BY recorded_at DESC, created_at DESC LIMIT " + limit, pid);
        }
        String marks = String.join(",", Collections.nCopies(categories.size(), "?"));
        List<Object> args = new ArrayList<>(List.of(pid));
        args.addAll(categories);
        return db.list("SELECT * FROM health_records WHERE patient_id = ? "
                + "AND category IN (" + marks + ") ORDER BY recorded_at DESC, created_at DESC LIMIT "
                + limit, args.toArray());
    }

    private List<Map<String, Object>> observations(String pid, int limit) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM observations WHERE patient_id = ? "
                + "ORDER BY observed_at DESC LIMIT " + limit, pid)) out.add(Views.observation(row));
        return out;
    }

    private List<Map<String, Object>> allergies(String pid) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM allergies WHERE patient_id = ? "
                + "ORDER BY created_at DESC", pid)) out.add(Views.allergy(row));
        return out;
    }

    private List<Map<String, Object>> medications(String pid) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM medications WHERE patient_id = ? "
                + "ORDER BY created_at DESC", pid)) out.add(Views.medication(row));
        return out;
    }

    private List<Map<String, Object>> documents(String pid) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM documents WHERE patient_id = ? "
                + "ORDER BY created_at DESC", pid)) out.add(Views.document(row, null));
        return out;
    }

    private List<Map<String, Object>> timeline(String pid, int limit) {
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM timeline_events "
                + "WHERE patient_id = ? ORDER BY occurred_at DESC LIMIT " + limit, pid)) {
            out.add(Views.timeline(row));
        }
        return out;
    }
}
