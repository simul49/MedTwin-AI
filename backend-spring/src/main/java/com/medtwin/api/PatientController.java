package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/** Patient-owned Digital Twin data: records, observations, allergies, medications, documents. */
@RestController
public class PatientController {
    private static final Set<String> CATEGORIES = Set.of(
            "CONDITION", "ALLERGY", "MEDICATION", "LAB_RESULT", "PROCEDURE",
            "IMMUNIZATION", "NOTE", "FAMILY_HISTORY", "VITAL");
    private static final Set<String> MIME = Set.of(
            "application/pdf", "image/png", "image/jpeg");
    private static final Set<String> EXTENSIONS = Set.of(".pdf", ".png", ".jpg", ".jpeg");

    private final Db db;
    private final Access access;
    private final Audit audit;
    private final AiClient ai;
    private final Storage storage;

    public PatientController(Db db, Access access, Audit audit, AiClient ai, Storage storage) {
        this.db = db;
        this.access = access;
        this.audit = audit;
        this.ai = ai;
        this.storage = storage;
    }

    // ------------------------------------------------------------------ twin --
    @GetMapping("/patient/digital-twin/")
    public Map<String, Object> digitalTwin() {
        access.require("PATIENT");
        String pid = Ctx.user().id;
        Map<String, Object> user = db.require("SELECT * FROM users WHERE id = ?", pid);
        Map<String, Object> profile = db.one("SELECT * FROM patient_profiles WHERE user_id = ?", pid);

        Map<String, Object> counts = J.map(
                "records", db.count("SELECT COUNT(*) FROM health_records WHERE patient_id = ?", pid),
                "observations", db.count("SELECT COUNT(*) FROM observations WHERE patient_id = ?", pid),
                "allergies", db.count("SELECT COUNT(*) FROM allergies WHERE patient_id = ?", pid),
                "medications", db.count("SELECT COUNT(*) FROM medications WHERE patient_id = ?", pid),
                "documents", db.count("SELECT COUNT(*) FROM documents WHERE patient_id = ?", pid),
                "timeline", db.count("SELECT COUNT(*) FROM timeline_events WHERE patient_id = ?", pid));

        List<String> missing = new ArrayList<>();
        if (counts.get("allergies").equals(0L)) missing.add("allergies");
        if (counts.get("medications").equals(0L)) missing.add("medications");
        if (counts.get("observations").equals(0L)) missing.add("observations");
        Map<String, Object> last = db.one("SELECT updated_at FROM health_records "
                + "WHERE patient_id = ? ORDER BY updated_at DESC LIMIT 1", pid);
        Map<String, Object> freshness = J.map(
                "lastUpdated", last == null ? null : J.iso(last.get("updated_at")),
                "unverifiedCount", db.count("SELECT COUNT(*) FROM health_records "
                        + "WHERE patient_id = ? AND verification_status = 'UNVERIFIED'", pid),
                "missingSections", missing);

        List<Map<String, Object>> consents = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM consent_grants "
                + "WHERE patient_id = ? ORDER BY created_at DESC", pid)) {
            consents.add(Views.grant(db, row));
        }

        return J.map(
                "patient", Views.user(db, user, true),
                "profile", profile == null ? J.map() : Views.patientProfile(profile),
                "counts", counts,
                "records", records(pid, 50),
                "observations", observations(pid, 20),
                "allergies", allergies(pid, 20),
                "medications", medications(pid, 20),
                "timeline", timeline(pid, null, 30),
                "freshness", freshness,
                "consents", consents);
    }

    // --------------------------------------------------------------- records --
    @GetMapping("/patient/records/")
    public Map<String, Object> listRecords(@RequestParam(required = false) String category,
                                           @RequestParam(required = false) String q) {
        access.require("PATIENT");
        String pid = Ctx.user().id;
        StringBuilder sql = new StringBuilder(
                "SELECT * FROM health_records WHERE patient_id = ?");
        List<Object> args = new ArrayList<>(List.of(pid));
        if (category != null && CATEGORIES.contains(category.toUpperCase())) {
            sql.append(" AND category = ?");
            args.add(category.toUpperCase());
        }
        if (q != null && !q.isBlank()) {
            sql.append(" AND title LIKE ?");
            args.add("%" + q.trim() + "%");
        }
        sql.append(" ORDER BY recorded_at DESC, created_at DESC LIMIT 100");
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql.toString(), args.toArray())) {
            results.add(Views.record(row));
        }
        return J.map("results", results);
    }

    @PostMapping("/patient/records/")
    public ResponseEntity<Object> createRecord(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT", "DOCTOR");
        Principal user = Ctx.user();
        String patientId = user.role.equals("DOCTOR")
                ? J.s(access.resolvePatient(user, J.gs(body, "patientId")).get("id"))
                : user.id;
        String category = J.gs(body, "category").isEmpty()
                ? "NOTE" : J.gs(body, "category").toUpperCase();
        if (!CATEGORIES.contains(category)) throw ApiError.bad("Unknown record category.");
        String title = J.gs(body, "title").trim();
        if (title.isEmpty()) throw ApiError.bad("A title is required.");
        boolean clinician = user.role.equals("DOCTOR");
        String id = J.uuid();
        db.exec("INSERT INTO health_records (id, patient_id, category, title, summary, payload, "
                        + "source_type, verification_status, author_id, recorded_at, created_at, updated_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                id, patientId, category, title, blankToNull(J.gs(body, "summary").trim()),
                J.g(body, "payload") == null ? null : J.toJson(J.g(body, "payload")),
                clinician ? "CLINICIAN" : "USER",
                clinician ? "CLINICIAN_CONFIRMED" : "USER_CONFIRMED",
                user.id, J.ts(), J.ts(), J.ts());
        db.exec("INSERT INTO timeline_events (id, patient_id, event_type, title, description, "
                        + "occurred_at, source_type, source_id, created_at) "
                        + "VALUES (?, ?, 'RECORD_ADDED', ?, ?, ?, ?, ?, ?)",
                J.uuid(), patientId, title,
                blankToNull(J.gs(body, "summary").substring(0, Math.min(500, J.gs(body, "summary").length()))),
                J.ts(), clinician ? "CLINICIAN" : "USER", id, J.ts());
        audit.log("RECORD_CREATE", "health_record", id, "SUCCESS",
                J.map("category", category, "patientId", patientId));
        return ResponseEntity.status(201).body(
                Views.record(db.require("SELECT * FROM health_records WHERE id = ?", id)));
    }

    @GetMapping("/patient/records/{id}/")
    public Map<String, Object> getRecord(@PathVariable String id) {
        return Views.record(visibleRecord(id));
    }

    @PatchMapping("/patient/records/{id}/")
    public Map<String, Object> updateRecord(@PathVariable String id,
                                            @RequestBody(required = false) Map<String, Object> body) {
        visibleRecord(id);
        Map<String, String> columns = new LinkedHashMap<>();
        columns.put("title", "title");
        columns.put("summary", "summary");
        columns.put("category", "category");
        columns.put("payload", "payload");
        columns.put("verificationStatus", "verification_status");
        columns.put("verification_status", "verification_status");
        dynamicUpdate("health_records", id, body, columns);
        audit.log("RECORD_UPDATE", "health_record", id, "SUCCESS", null);
        return Views.record(db.require("SELECT * FROM health_records WHERE id = ?", id));
    }

    @DeleteMapping("/patient/records/{id}/")
    public ResponseEntity<Void> deleteRecord(@PathVariable String id) {
        visibleRecord(id);
        if (Ctx.user().role.equals("DOCTOR")) {
            throw new ApiError(403, "Doctors cannot delete patient records.");
        }
        audit.log("RECORD_DELETE", "health_record", id, "SUCCESS", null);
        db.exec("DELETE FROM health_records WHERE id = ?", id);
        return ResponseEntity.noContent().build();
    }

    private Map<String, Object> visibleRecord(String id) {
        Map<String, Object> row = db.one("SELECT * FROM health_records WHERE id = ?", id);
        if (row == null) throw ApiError.notFound("Not found.");
        Principal user = Ctx.user();
        String patientId = J.s(row.get("patient_id"));
        if (user.role.equals("PATIENT") && !user.id.equals(patientId)) {
            throw ApiError.notFound("Not found.");
        }
        if (user.role.equals("DOCTOR") && access.scope(user, patientId).isEmpty()) {
            throw ApiError.notFound("Not found.");
        }
        return row;
    }

    // -------------------------------------------------------------- read sets --
    @GetMapping("/patient/timeline/")
    public Map<String, Object> listTimeline(@RequestParam(required = false) String type) {
        access.require("PATIENT");
        return J.map("results", timeline(Ctx.user().id, type, 100));
    }

    @GetMapping("/patient/observations/")
    public Map<String, Object> listObservations() {
        access.require("PATIENT");
        return J.map("results", observations(Ctx.user().id, 100));
    }

    @GetMapping("/patient/allergies/")
    public Map<String, Object> listAllergies() {
        access.require("PATIENT");
        return J.map("results", allergies(Ctx.user().id, 0));
    }

    @PostMapping("/patient/allergies/")
    public ResponseEntity<Object> createAllergy(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        String substance = J.gs(body, "substance").trim();
        if (substance.isEmpty()) throw ApiError.bad("Name the substance.");
        String id = J.uuid();
        db.exec("INSERT INTO allergies (id, patient_id, substance, reaction, severity, status, "
                        + "source_type, created_at) VALUES (?, ?, ?, ?, ?, ?, 'USER', ?)",
                id, Ctx.user().id, substance, blankToNull(J.gs(body, "reaction").trim()),
                upperOr(J.gs(body, "severity"), "UNKNOWN"),
                upperOr(J.gs(body, "status"), "ACTIVE"), J.ts());
        audit.log("ALLERGY_CREATE", "allergy", id, "SUCCESS", null);
        return ResponseEntity.status(201).body(
                Views.allergy(db.require("SELECT * FROM allergies WHERE id = ?", id)));
    }

    @PatchMapping("/patient/allergies/{id}/")
    public Map<String, Object> updateAllergy(@PathVariable String id,
                                             @RequestBody(required = false) Map<String, Object> body) {
        owned("allergies", id);
        dynamicUpdate("allergies", id, body, Map.of(
                "substance", "substance", "reaction", "reaction",
                "severity", "severity", "status", "status"));
        if (J.bool(J.g(body, "reviewed"))) {
            db.exec("UPDATE allergies SET reviewed_at = ? WHERE id = ?", J.ts(), id);
        }
        return Views.allergy(db.require("SELECT * FROM allergies WHERE id = ?", id));
    }

    @DeleteMapping("/patient/allergies/{id}/")
    public ResponseEntity<Void> deleteAllergy(@PathVariable String id) {
        owned("allergies", id);
        db.exec("DELETE FROM allergies WHERE id = ?", id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/patient/medications/")
    public Map<String, Object> listMedications() {
        access.require("PATIENT");
        return J.map("results", medications(Ctx.user().id, 0));
    }

    @PostMapping("/patient/medications/")
    public ResponseEntity<Object> createMedication(@RequestBody(required = false) Map<String, Object> body) {
        access.require("PATIENT");
        String name = J.gs(body, "name").trim();
        if (name.isEmpty()) throw ApiError.bad("Name the medication.");
        String id = J.uuid();
        db.exec("INSERT INTO medications (id, patient_id, name, dose, frequency, route, status, "
                        + "started_at, source_type, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'USER', ?)",
                id, Ctx.user().id, name, blankToNull(J.gs(body, "dose").trim()),
                blankToNull(J.gs(body, "frequency").trim()), blankToNull(J.gs(body, "route").trim()),
                upperOr(J.gs(body, "status"), "ACTIVE"),
                blankToNull(firstNonBlank(body, "started_at", "startedAt")), J.ts());
        audit.log("MEDICATION_CREATE", "medication", id, "SUCCESS", null);
        return ResponseEntity.status(201).body(
                Views.medication(db.require("SELECT * FROM medications WHERE id = ?", id)));
    }

    @PatchMapping("/patient/medications/{id}/")
    public Map<String, Object> updateMedication(@PathVariable String id,
                                                @RequestBody(required = false) Map<String, Object> body) {
        owned("medications", id);
        Map<String, String> columns = new LinkedHashMap<>();
        for (String key : List.of("name", "dose", "frequency", "route", "status")) columns.put(key, key);
        columns.put("started_at", "started_at");
        columns.put("startedAt", "started_at");
        columns.put("ended_at", "ended_at");
        columns.put("endedAt", "ended_at");
        dynamicUpdate("medications", id, body, columns);
        return Views.medication(db.require("SELECT * FROM medications WHERE id = ?", id));
    }

    @DeleteMapping("/patient/medications/{id}/")
    public ResponseEntity<Void> deleteMedication(@PathVariable String id) {
        owned("medications", id);
        db.exec("DELETE FROM medications WHERE id = ?", id);
        return ResponseEntity.noContent().build();
    }

    // ------------------------------------------------------------- documents --
    @GetMapping("/patient/documents/")
    public Map<String, Object> listDocuments() {
        access.require("PATIENT");
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM documents WHERE patient_id = ? "
                + "ORDER BY created_at DESC", Ctx.user().id)) {
            results.add(Views.document(row, null));
        }
        return J.map("results", results);
    }

    @PostMapping("/patient/documents/")
    public ResponseEntity<Object> uploadDocument(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "category", required = false) String category) throws IOException {
        access.require("PATIENT");
        if (file == null || file.isEmpty()) throw ApiError.bad("Choose a file to upload.");
        String name = file.getOriginalFilename() == null ? "document" : file.getOriginalFilename();
        int dot = name.lastIndexOf('.');
        String suffix = dot >= 0 ? name.substring(dot).toLowerCase() : "";
        String stem = dot >= 0 ? name.substring(0, dot) : name;
        if (!EXTENSIONS.contains(suffix)) {
            throw ApiError.bad("Unsupported file type '" + suffix + "'. Allowed: PDF, PNG, JPG.");
        }
        String mime = file.getContentType();
        if (mime == null || !MIME.contains(mime)) {
            throw ApiError.bad("File contents do not match an allowed type.");
        }
        if (file.getSize() > 15L * 1024 * 1024) {
            throw ApiError.bad("File exceeds the 15 MB limit.");
        }

        String patientId = Ctx.user().id;
        String safe = stem.replaceAll("[^A-Za-z0-9._-]+", "_");
        if (safe.length() > 60) safe = safe.substring(0, 60);
        if (safe.isEmpty()) safe = "document";
        String relative = patientId + "/" + J.uuid() + "_" + safe + suffix;
        Path target = storage.resolve(relative);
        Files.createDirectories(target.getParent());
        Files.write(target, file.getBytes());

        Map<String, Object> extracted;
        try {
            Object result = ai.post("/internal/extract/", J.map(
                    "path", target.toString(), "mimeType", mime));
            @SuppressWarnings("unchecked")
            Map<String, Object> typed = result instanceof Map<?, ?> ? (Map<String, Object>) result : J.map();
            extracted = typed;
        } catch (ApiError exc) {
            extracted = J.map("text", "", "pageCount", 0,
                    "error", "Extraction service unavailable.", "fields", List.of(),
                    "sha256", "");
        }
        String text = J.s(extracted.get("text"));
        String error = J.s(extracted.get("error"));
        int pageCount = J.gi(extracted, "pageCount", 0);
        String id = J.uuid();
        db.exec("INSERT INTO documents (id, owner_id, patient_id, name, mime_type, size_bytes, "
                        + "storage_path, sha256, category, processing_status, processing_error, "
                        + "extracted_text, page_count, uploaded_by, created_at, processed_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                id, patientId, patientId, name.substring(0, Math.min(255, name.length())),
                mime, file.getSize(), relative, blankToNull(J.s(extracted.get("sha256"))),
                (category == null || category.isBlank() ? "OTHER" : category.toUpperCase())
                        .substring(0, Math.min(40, (category == null || category.isBlank()
                                ? "OTHER" : category.toUpperCase()).length())),
                error.isEmpty() ? "PROCESSED" : "FAILED", blankToNull(error),
                text.isEmpty() ? null : text, pageCount == 0 ? null : pageCount,
                patientId, J.ts(), J.ts());

        Object fields = extracted.get("fields");
        if (fields instanceof List<?> items) {
            for (Object item : items) {
                if (!(item instanceof Map<?, ?> raw)) continue;
                @SuppressWarnings("unchecked")
                Map<String, Object> field = (Map<String, Object>) raw;
                db.exec("INSERT INTO document_extractions (id, document_id, field_name, label, "
                                + "value, confidence, review_status, evidence, created_at) "
                                + "VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)",
                        J.uuid(), id, J.s(field.get("field_name")), J.s(field.get("label")),
                        J.s(field.get("value")), J.num(field.get("confidence")),
                        J.s(field.get("evidence")), J.ts());
            }
        }
        db.exec("INSERT INTO timeline_events (id, patient_id, event_type, title, description, "
                        + "occurred_at, source_type, source_id, created_at) "
                        + "VALUES (?, ?, 'DOCUMENT_UPLOADED', ?, ?, ?, 'EXTRACTED', ?, ?)",
                J.uuid(), patientId, truncate("Uploaded " + name, 200),
                (error.isEmpty() ? text.length() + " characters extracted." : error)
                        .substring(0, Math.min(500, (error.isEmpty()
                                ? text.length() + " characters extracted." : error).length())),
                J.ts(), id, J.ts());
        audit.log("DOCUMENT_UPLOAD", "document", id, "SUCCESS",
                J.map("size", file.getSize(), "status", error.isEmpty() ? "PROCESSED" : "FAILED"));

        List<Map<String, Object>> rows = db.list("SELECT * FROM document_extractions "
                + "WHERE document_id = ? ORDER BY field_name", id);
        return ResponseEntity.status(201).body(
                Views.document(db.require("SELECT * FROM documents WHERE id = ?", id), rows));
    }

    @GetMapping("/patient/documents/{id}/")
    public Map<String, Object> getDocument(@PathVariable String id) {
        visibleDocument(id);
        return Views.document(db.require("SELECT * FROM documents WHERE id = ?", id),
                db.list("SELECT * FROM document_extractions WHERE document_id = ? ORDER BY field_name", id));
    }

    @DeleteMapping("/patient/documents/{id}/")
    public ResponseEntity<Void> deleteDocument(@PathVariable String id) throws IOException {
        Map<String, Object> row = visibleDocument(id);
        if (!Ctx.user().role.equals("PATIENT")) {
            throw new ApiError(403, "Only the patient can delete this document.");
        }
        Files.deleteIfExists(storage.resolve(J.s(row.get("storage_path"))));
        audit.log("DOCUMENT_DELETE", "document", id, "SUCCESS", null);
        db.exec("DELETE FROM document_extractions WHERE document_id = ?", id);
        db.exec("DELETE FROM documents WHERE id = ?", id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/patient/documents/{id}/file/")
    public ResponseEntity<byte[]> downloadDocument(@PathVariable String id) throws IOException {
        Map<String, Object> row = visibleDocument(id);
        Principal user = Ctx.user();
        if (user.role.equals("DOCTOR")) {
            List<String> scope = access.scope(user, J.s(row.get("patient_id")));
            if (!access.has(scope, "documents")) throw ApiError.notFound("Not found.");
        }
        Path path = storage.resolve(J.s(row.get("storage_path")));
        if (!Files.exists(path)) throw ApiError.notFound("Not found.");
        audit.log("DOCUMENT_DOWNLOAD", "document", id, "SUCCESS", null);
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment()
                                .filename(J.s(row.get("name")), StandardCharsets.UTF_8)
                                .build().toString())
                .contentType(MediaType.parseMediaType(J.s(row.get("mime_type"))))
                .body(Files.readAllBytes(path));
    }

    @PostMapping("/patient/documents/{documentId}/extractions/{extractionId}/review/")
    public Map<String, Object> reviewExtraction(@PathVariable String documentId,
                                                @PathVariable String extractionId,
                                                @RequestBody(required = false) Map<String, Object> body) {
        Map<String, Object> document = db.one(
                "SELECT id FROM documents WHERE id = ? AND patient_id = ?", documentId, Ctx.user().id);
        Map<String, Object> item = db.one("SELECT * FROM document_extractions "
                + "WHERE id = ? AND document_id = ?", extractionId, documentId);
        if (document == null || item == null) throw ApiError.notFound("Not found.");
        String status = J.gs(body, "status").toUpperCase();
        if (!Set.of("CONFIRMED", "CORRECTED", "REJECTED").contains(status)) {
            throw ApiError.bad("Status must be CONFIRMED, CORRECTED or REJECTED.");
        }
        if (status.equals("CORRECTED")) {
            String value = J.gs(body, "value");
            String next = value.isEmpty() ? J.s(item.get("value")) : value;
            db.exec("UPDATE document_extractions SET value = ?, review_status = ? WHERE id = ?",
                    next.substring(0, Math.min(255, next.length())), status, extractionId);
        } else {
            db.exec("UPDATE document_extractions SET review_status = ? WHERE id = ?",
                    status, extractionId);
        }
        audit.log("EXTRACTION_REVIEW", "document_extraction", extractionId, "SUCCESS",
                J.map("status", status));
        return Views.extraction(db.require(
                "SELECT * FROM document_extractions WHERE id = ?", extractionId));
    }

    private Map<String, Object> visibleDocument(String id) {
        Map<String, Object> row = db.one("SELECT * FROM documents WHERE id = ?", id);
        if (row == null) throw ApiError.notFound("Not found.");
        Principal user = Ctx.user();
        String patientId = J.s(row.get("patient_id"));
        if (user.role.equals("PATIENT") && !user.id.equals(patientId)) {
            throw ApiError.notFound("Not found.");
        }
        if (user.role.equals("DOCTOR") && access.scope(user, patientId).isEmpty()) {
            throw ApiError.notFound("Not found.");
        }
        return row;
    }

    // -------------------------------------------------------- export / erase --
    @GetMapping("/patient/export/")
    public Map<String, Object> exportData() {
        access.require("PATIENT");
        String pid = Ctx.user().id;
        Map<String, Object> profile = db.one("SELECT * FROM patient_profiles WHERE user_id = ?", pid);
        audit.log("DATA_EXPORT", "patient", pid, "SUCCESS", null);
        List<Map<String, Object>> docs = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM documents WHERE patient_id = ? "
                + "ORDER BY created_at DESC", pid)) docs.add(Views.document(row, null));
        return J.map(
                "exportedAt", J.nowIso(),
                "patient", Views.user(db, db.require("SELECT * FROM users WHERE id = ?", pid), true),
                "profile", profile == null ? J.map() : Views.patientProfile(profile),
                "records", records(pid, 0),
                "observations", observations(pid, 0),
                "allergies", allergies(pid, 0),
                "medications", medications(pid, 0),
                "documents", docs,
                "timeline", timeline(pid, null, 0));
    }

    @DeleteMapping("/patient/data/")
    public Map<String, Object> deleteData() throws IOException {
        access.require("PATIENT");
        String pid = Ctx.user().id;
        for (Map<String, Object> row : db.list("SELECT storage_path FROM documents "
                + "WHERE patient_id = ?", pid)) {
            Files.deleteIfExists(storage.resolve(J.s(row.get("storage_path"))));
        }
        db.exec("DELETE FROM document_extractions WHERE document_id IN "
                + "(SELECT id FROM documents WHERE patient_id = ?)", pid);
        for (String table : List.of("health_records", "observations", "allergies",
                "medications", "timeline_events", "documents")) {
            db.exec("DELETE FROM " + table + " WHERE patient_id = ?", pid);
        }
        audit.log("DATA_DELETE", "patient", pid, "SUCCESS", null);
        return J.map("ok", true);
    }

    // --------------------------------------------------------------- helpers --
    private List<Map<String, Object>> records(String pid, int limit) {
        String sql = "SELECT * FROM health_records WHERE patient_id = ? "
                + "ORDER BY recorded_at DESC, created_at DESC" + (limit > 0 ? " LIMIT " + limit : "");
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql, pid)) out.add(Views.record(row));
        return out;
    }

    private List<Map<String, Object>> observations(String pid, int limit) {
        String sql = "SELECT * FROM observations WHERE patient_id = ? ORDER BY observed_at DESC"
                + (limit > 0 ? " LIMIT " + limit : "");
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql, pid)) out.add(Views.observation(row));
        return out;
    }

    private List<Map<String, Object>> allergies(String pid, int limit) {
        String sql = "SELECT * FROM allergies WHERE patient_id = ? ORDER BY created_at DESC"
                + (limit > 0 ? " LIMIT " + limit : "");
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql, pid)) out.add(Views.allergy(row));
        return out;
    }

    private List<Map<String, Object>> medications(String pid, int limit) {
        String sql = "SELECT * FROM medications WHERE patient_id = ? ORDER BY created_at DESC"
                + (limit > 0 ? " LIMIT " + limit : "");
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql, pid)) out.add(Views.medication(row));
        return out;
    }

    private List<Map<String, Object>> timeline(String pid, String type, int limit) {
        StringBuilder sql = new StringBuilder("SELECT * FROM timeline_events WHERE patient_id = ?");
        List<Object> args = new ArrayList<>(List.of(pid));
        if (type != null && !type.isBlank()) {
            sql.append(" AND event_type = ?");
            args.add(type);
        }
        sql.append(" ORDER BY occurred_at DESC");
        if (limit > 0) sql.append(" LIMIT ").append(limit);
        List<Map<String, Object>> out = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql.toString(), args.toArray())) {
            out.add(Views.timeline(row));
        }
        return out;
    }

    private void owned(String table, String id) {
        Map<String, Object> row = db.one(
                "SELECT id FROM " + table + " WHERE id = ? AND patient_id = ?", id, Ctx.user().id);
        if (row == null) throw ApiError.notFound("Not found.");
    }

    private void dynamicUpdate(String table, String id, Map<String, Object> body,
                               Map<String, String> columns) {
        List<String> sets = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, String> entry : columns.entrySet()) {
            if (!body.containsKey(entry.getKey()) || sets.contains(entry.getValue() + " = ?")) continue;
            Object value = body.get(entry.getKey());
            sets.add(entry.getValue() + " = ?");
            args.add(entry.getValue().equals("payload")
                    ? (value == null ? null : J.toJson(value))
                    : value == null ? null : J.s(value));
        }
        if (sets.isEmpty()) return;
        args.add(id);
        db.exec("UPDATE " + table + " SET " + String.join(", ", sets) + " WHERE id = ?",
                args.toArray());
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private static String truncate(String value, int max) {
        return value.length() <= max ? value : value.substring(0, max);
    }

    private static String upperOr(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value.toUpperCase();
    }

    private static String firstNonBlank(Map<String, Object> body, String a, String b) {
        String value = J.gs(body, a);
        return value.isBlank() ? J.gs(body, b) : value;
    }
}
