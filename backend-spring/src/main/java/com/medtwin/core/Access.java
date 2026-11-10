package com.medtwin.core;

import org.springframework.stereotype.Service;

import java.sql.Timestamp;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;

/** Role and consent enforcement. A doctor without a live grant always gets 404. */
@Service
public class Access {
    public static final List<String> SCOPE_OPTIONS = List.of(
            "profile", "conditions", "medications", "allergies",
            "lab_results", "documents", "timeline");

    private static final Map<String, List<String>> SCOPE_CATEGORIES = Map.of(
            "conditions", List.of("CONDITION", "FAMILY_HISTORY"),
            "medications", List.of("MEDICATION"),
            "allergies", List.of("ALLERGY"),
            "lab_results", List.of("LAB_RESULT", "VITAL"));

    private final Db db;
    private final Audit audit;

    public Access(Db db, Audit audit) {
        this.db = db;
        this.audit = audit;
    }

    public void require(String... roles) {
        Principal user = Ctx.user();
        if (!Arrays.asList(roles).contains(user.role)) {
            audit.log("ACCESS_DENIED", "role", "", "DENIED",
                    J.map("required", Arrays.asList(roles)));
            throw ApiError.forbidden();
        }
    }

    public boolean has(List<String> scope, String key) {
        return scope.contains("all") || scope.contains(key);
    }

    public Map<String, Object> activeGrant(String doctorId, String patientId) {
        return db.one("SELECT * FROM consent_grants WHERE doctor_id = ? AND patient_id = ? "
                + "AND status = 'ACTIVE' ORDER BY created_at DESC LIMIT 1", doctorId, patientId);
    }

    public boolean grantIsLive(Map<String, Object> grant) {
        if (grant == null || !"ACTIVE".equals(J.s(grant.get("status")))) return false;
        Object expires = grant.get("expires_at");
        if (expires == null) return true;
        if (expires instanceof Timestamp t) return t.after(J.ts());
        return true;
    }

    public List<String> scope(Principal user, String patientId) {
        if (user.role.equals("ADMIN")) return List.of("all");
        if (user.role.equals("PATIENT") && user.id.equals(patientId)) return List.of("all");
        Map<String, Object> grant = activeGrant(user.id, patientId);
        if (!grantIsLive(grant)) return List.of();
        return J.strings(grant.get("scope"));
    }

    public Map<String, Object> resolvePatient(Principal user, String patientId) {
        Map<String, Object> patient = db.one(
                "SELECT * FROM users WHERE id = ? AND role = 'PATIENT'", patientId);
        if (patient == null) throw ApiError.notFound("Patient not found.");
        if (user.role.equals("ADMIN")) return patient;
        if (user.role.equals("PATIENT")) {
            if (!user.id.equals(patientId)) throw ApiError.notFound("Patient not found.");
            return patient;
        }
        if (user.role.equals("DOCTOR") && grantIsLive(activeGrant(user.id, patientId))) {
            return patient;
        }
        audit.log("ACCESS_DENIED", "patient", patientId, "DENIED",
                J.map("reason", "no_active_grant"));
        throw ApiError.notFound("Patient not found.");
    }

    public List<String> categories(List<String> scope) {
        if (scope.contains("all")) {
            return List.of("CONDITION", "ALLERGY", "MEDICATION", "LAB_RESULT", "PROCEDURE",
                    "IMMUNIZATION", "NOTE", "FAMILY_HISTORY", "VITAL");
        }
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (String key : scope) out.addAll(SCOPE_CATEGORIES.getOrDefault(key, List.of()));
        return new ArrayList<>(out);
    }

    public List<String> parseScope(Object raw) {
        List<String> allowed = new ArrayList<>();
        for (String key : J.strings(raw)) {
            if (SCOPE_OPTIONS.contains(key) || key.equals("all")) allowed.add(key);
        }
        return allowed.isEmpty() ? List.of("profile", "conditions") : allowed;
    }
}
