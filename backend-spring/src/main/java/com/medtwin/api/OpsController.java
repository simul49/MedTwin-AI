package com.medtwin.api;

import com.medtwin.core.*;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.*;

/** Health, administration, governance and audit review. */
@RestController
public class OpsController {
    private final Db db;
    private final Access access;
    private final Audit audit;
    private final AiClient ai;

    public OpsController(Db db, Access access, Audit audit, AiClient ai) {
        this.db = db;
        this.access = access;
        this.audit = audit;
        this.ai = ai;
    }

    @GetMapping("/health/")
    public Map<String, Object> health() {
        return J.map(
                "service", "medtwin-spring-boot",
                "version", "1.0.0",
                "database", db.reachable() ? "ok" : "unavailable: database error",
                "aiProvider", ai.model(),
                "time", J.nowIso());
    }

    @GetMapping("/admin/users/")
    public Map<String, Object> users(@RequestParam(required = false) String role,
                                     @RequestParam(required = false) String q) {
        access.require("ADMIN");
        StringBuilder sql = new StringBuilder("SELECT * FROM users WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (role != null && !role.isBlank()) {
            sql.append(" AND role = ?");
            args.add(role.toUpperCase());
        }
        if (q != null && !q.isBlank()) {
            sql.append(" AND (name LIKE ? OR email LIKE ?)");
            args.add("%" + q.trim() + "%");
            args.add("%" + q.trim() + "%");
        }
        sql.append(" ORDER BY created_at DESC LIMIT 200");
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql.toString(), args.toArray())) {
            results.add(Views.user(db, row, false));
        }
        audit.log("ADMIN_USER_LIST", "user", "", "SUCCESS", null);
        return J.map("results", results);
    }

    @PatchMapping("/admin/users/{id}/")
    public Map<String, Object> updateUser(@PathVariable String id,
                                          @RequestBody(required = false) Map<String, Object> body) {
        access.require("ADMIN");
        db.require("SELECT * FROM users WHERE id = ?", id);
        List<String> changed = new ArrayList<>();
        List<String> sets = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        if (body != null && body.containsKey("isActive")) {
            sets.add("is_active = ?");
            args.add(J.bool(body.get("isActive")) ? 1 : 0);
            changed.add("isActive");
        }
        if (body != null && body.containsKey("isVerified")) {
            sets.add("is_verified = ?");
            args.add(J.bool(body.get("isVerified")) ? 1 : 0);
            changed.add("isVerified");
        }
        if (body != null && Set.of("PATIENT", "DOCTOR", "ADMIN")
                .contains(J.gs(body, "role"))) {
            sets.add("role = ?");
            args.add(J.gs(body, "role"));
            changed.add("role");
        }
        if (!sets.isEmpty()) {
            args.add(id);
            db.exec("UPDATE users SET " + String.join(", ", sets) + " WHERE id = ?", args.toArray());
        }
        if (body != null && body.containsKey("verificationStatus")) {
            String status = J.gs(body, "verificationStatus").toUpperCase();
            int updated = db.exec("UPDATE doctor_profiles SET verification_status = ?, "
                            + "verified_at = ? WHERE user_id = ?",
                    status, status.equals("VERIFIED") ? J.ts() : null, id);
            if (updated > 0) changed.add("verificationStatus");
        }
        audit.log("ADMIN_USER_UPDATE", "user", id, "SUCCESS", J.map("fields", changed));
        return Views.user(db, db.require("SELECT * FROM users WHERE id = ?", id), false);
    }

    @GetMapping("/admin/audit-logs/")
    public Map<String, Object> auditLogs(@RequestParam(required = false) String action,
                                         @RequestParam(required = false) String outcome,
                                         @RequestParam(required = false) String actor) {
        access.require("ADMIN");
        StringBuilder sql = new StringBuilder("SELECT * FROM audit_logs WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (action != null && !action.isBlank()) {
            sql.append(" AND action = ?");
            args.add(action);
        }
        if (outcome != null && !outcome.isBlank()) {
            sql.append(" AND outcome = ?");
            args.add(outcome.toUpperCase());
        }
        if (actor != null && !actor.isBlank()) {
            sql.append(" AND actor_email LIKE ?");
            args.add("%" + actor.trim() + "%");
        }
        sql.append(" ORDER BY created_at DESC LIMIT 300");
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list(sql.toString(), args.toArray())) {
            results.add(Views.audit(row));
        }
        audit.log("AUDIT_READ", "audit_log", "", "SUCCESS",
                J.map("filters", J.map("action", action == null ? "" : action,
                        "outcome", outcome == null ? "" : outcome)));
        return J.map("results", results);
    }

    @GetMapping("/admin/consent-grants/")
    public Map<String, Object> consentGrants() {
        access.require("ADMIN");
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list(
                "SELECT * FROM consent_grants ORDER BY created_at DESC LIMIT 200")) {
            results.add(Views.grant(db, row));
        }
        return J.map("results", results);
    }

    @GetMapping("/admin/knowledge-sources/")
    public Map<String, Object> sources() {
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM knowledge_sources ORDER BY title")) {
            results.add(Views.source(db, row));
        }
        return J.map("results", results);
    }

    @PostMapping("/admin/knowledge-sources/")
    public ResponseEntity<Object> createSource(@RequestBody(required = false) Map<String, Object> body) {
        access.require("ADMIN");
        String title = J.gs(body, "title").trim();
        if (title.isEmpty()) throw ApiError.bad("A title is required.");
        String id = J.uuid();
        db.exec("INSERT INTO knowledge_sources (id, title, publisher, version, source_url, "
                        + "category, license_status, review_status, ingested_at, created_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                id, title.substring(0, Math.min(255, title.length())),
                blankToNull(J.gs(body, "publisher").trim()),
                blankToNull(J.gs(body, "version").trim()),
                blankToNull(J.gs(body, "sourceUrl").trim()),
                blankToNull(J.gs(body, "category").trim()),
                J.gs(body, "licenseStatus").isEmpty() ? "UNKNOWN" : J.gs(body, "licenseStatus").toUpperCase(),
                J.gs(body, "reviewStatus").isEmpty() ? "PENDING" : J.gs(body, "reviewStatus").toUpperCase(),
                J.ts(), J.ts());
        audit.log("KNOWLEDGE_SOURCE_CREATE", "knowledge_source", id, "SUCCESS", null);
        return ResponseEntity.status(201).body(Views.source(db,
                db.require("SELECT * FROM knowledge_sources WHERE id = ?", id)));
    }

    @PatchMapping("/admin/knowledge-sources/{id}/")
    public Map<String, Object> updateSource(@PathVariable String id,
                                            @RequestBody(required = false) Map<String, Object> body) {
        access.require("ADMIN");
        db.require("SELECT * FROM knowledge_sources WHERE id = ?", id);
        List<String> sets = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        if (body != null && body.containsKey("reviewStatus")) {
            sets.add("review_status = ?");
            args.add(J.gs(body, "reviewStatus").toUpperCase());
        }
        if (body != null && body.containsKey("licenseStatus")) {
            sets.add("license_status = ?");
            args.add(J.gs(body, "licenseStatus").toUpperCase());
        }
        if (!sets.isEmpty()) {
            args.add(id);
            db.exec("UPDATE knowledge_sources SET " + String.join(", ", sets) + " WHERE id = ?",
                    args.toArray());
        }
        audit.log("KNOWLEDGE_SOURCE_UPDATE", "knowledge_source", id, "SUCCESS", null);
        return Views.source(db, db.require("SELECT * FROM knowledge_sources WHERE id = ?", id));
    }

    @DeleteMapping("/admin/knowledge-sources/{id}/")
    public ResponseEntity<Void> deleteSource(@PathVariable String id) {
        access.require("ADMIN");
        db.require("SELECT * FROM knowledge_sources WHERE id = ?", id);
        audit.log("KNOWLEDGE_SOURCE_DELETE", "knowledge_source", id, "SUCCESS", null);
        db.exec("DELETE FROM knowledge_sources WHERE id = ?", id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/admin/system/health/")
    public Map<String, Object> systemHealth() {
        access.require("ADMIN");
        Timestamp dayAgo = Timestamp.valueOf(LocalDateTime.now(ZoneOffset.UTC).minusDays(1));
        Map<String, Object> counts = J.map(
                "users", db.count("SELECT COUNT(*) FROM users"),
                "knowledgeSources", db.count("SELECT COUNT(*) FROM knowledge_sources"),
                "knowledgeChunks", db.count("SELECT COUNT(*) FROM knowledge_chunks"),
                "consentGrants", db.count("SELECT COUNT(*) FROM consent_grants"),
                "activeGrants", db.count("SELECT COUNT(*) FROM consent_grants WHERE status = 'ACTIVE'"),
                "aiInteractions", db.count("SELECT COUNT(*) FROM ai_interactions"),
                "lowTrustResponses", db.count("SELECT COUNT(*) FROM ai_interactions WHERE trust_score < 60"),
                "auditEvents24h", db.count("SELECT COUNT(*) FROM audit_logs WHERE created_at >= ?", dayAgo),
                "deniedEvents24h", db.count("SELECT COUNT(*) FROM audit_logs "
                        + "WHERE created_at >= ? AND outcome = 'DENIED'", dayAgo));
        List<Map<String, Object>> models = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM model_versions")) {
            models.add(J.map(
                    "id", J.s(row.get("id")),
                    "name", J.s(row.get("name")),
                    "version", J.s(row.get("version")),
                    "provider", J.s(row.get("provider")),
                    "kind", J.s(row.get("kind")),
                    "isActive", J.bool(row.get("is_active"))));
        }
        audit.log("SYSTEM_HEALTH_READ", "system", "", "SUCCESS", null);
        return J.map(
                "database", db.reachable() ? "ok" : "unavailable: database error",
                "aiProvider", ai.model(),
                "counts", counts,
                "models", models,
                "generatedAt", J.nowIso());
    }

    @GetMapping("/admin/feature-flags/")
    public Map<String, Object> flags() {
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list("SELECT * FROM feature_flags")) {
            results.add(Views.flag(row));
        }
        return J.map("results", results);
    }

    @PatchMapping("/admin/feature-flags/{id}/")
    public Map<String, Object> updateFlag(@PathVariable String id,
                                          @RequestBody(required = false) Map<String, Object> body) {
        access.require("ADMIN");
        db.require("SELECT * FROM feature_flags WHERE id = ?", id);
        if (body != null && body.containsKey("isEnabled")) {
            db.exec("UPDATE feature_flags SET is_enabled = ? WHERE id = ?",
                    J.bool(body.get("isEnabled")) ? 1 : 0, id);
        }
        if (body != null && body.containsKey("status")) {
            db.exec("UPDATE feature_flags SET status = ? WHERE id = ?",
                    J.gs(body, "status").toUpperCase(), id);
        }
        Map<String, Object> row = db.require("SELECT * FROM feature_flags WHERE id = ?", id);
        audit.log("FEATURE_FLAG_UPDATE", "feature_flag", id, "SUCCESS",
                J.map("isEnabled", J.bool(row.get("is_enabled")), "status", J.s(row.get("status"))));
        return J.map("id", id, "isEnabled", J.bool(row.get("is_enabled")),
                "status", J.s(row.get("status")));
    }

    private static String blankToNull(String value) {
        return value == null || value.isBlank() ? null : value;
    }
}
