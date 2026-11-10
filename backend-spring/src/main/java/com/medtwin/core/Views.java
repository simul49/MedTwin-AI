package com.medtwin.core;

import java.sql.Date;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.Period;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** Exact camelCase response shapes, ported from the Django serializer modules. */
public final class Views {
    private Views() {
    }

    public static Map<String, Object> user(Db db, Map<String, Object> r, boolean detailed) {
        String id = J.s(r.get("id"));
        String name = J.s(r.get("name"));
        String email = J.s(r.get("email"));
        Map<String, Object> out = J.map(
                "id", id,
                "name", name,
                "email", email,
                "role", J.s(r.get("role")),
                "phone", J.s(r.get("phone")),
                "avatarColor", J.s(r.get("avatar_color")),
                "initials", new Principal(r).initials,
                "language", J.s(r.get("language")),
                "isActive", J.bool(r.get("is_active")),
                "isVerified", J.bool(r.get("is_verified")),
                "createdAt", J.iso(r.get("created_at")),
                "lastLoginAt", J.iso(r.get("last_login_at")));
        if (!detailed) return out;

        Map<String, Object> pp = db.one("SELECT * FROM patient_profiles WHERE user_id = ?", id);
        if (pp != null) out.put("patientProfile", patientProfile(pp));
        Map<String, Object> dp = db.one("SELECT * FROM doctor_profiles WHERE user_id = ?", id);
        if (dp != null) {
            out.put("doctorProfile", J.map(
                    "specialization", J.s(dp.get("specialization")),
                    "licenseNumber", J.s(dp.get("license_number")),
                    "hospital", J.s(dp.get("hospital")),
                    "department", J.s(dp.get("department")),
                    "bio", J.s(dp.get("bio")),
                    "verificationStatus", J.s(dp.get("verification_status"))));
        }
        List<String> roles = new ArrayList<>();
        for (Map<String, Object> row : db.list(
                "SELECT r.code FROM user_roles ur JOIN roles r ON r.id = ur.role_id "
                        + "WHERE ur.user_id = ?", id)) {
            roles.add(J.s(row.get("code")));
        }
        out.put("grantedRoles", roles);
        return out;
    }

    public static Map<String, Object> patientProfile(Map<String, Object> r) {
        return J.map(
                "dateOfBirth", J.iso(r.get("date_of_birth")),
                "age", age(r.get("date_of_birth")),
                "gender", J.s(r.get("gender")),
                "bloodType", J.s(r.get("blood_type")),
                "heightCm", J.num(r.get("height_cm")),
                "weightKg", J.num(r.get("weight_kg")),
                "city", J.s(r.get("city")),
                "emergencyContact", J.s(r.get("emergency_contact")),
                "summary", J.s(r.get("summary")));
    }

    private static Integer age(Object value) {
        LocalDate dob = null;
        if (value instanceof Date d) dob = d.toLocalDate();
        else if (value instanceof LocalDate l) dob = l;
        else if (value instanceof String s && s.matches("\\d{4}-\\d{2}-\\d{2}")) dob = LocalDate.parse(s);
        if (dob == null) return null;
        return Period.between(dob, LocalDate.now(ZoneOffset.UTC)).getYears();
    }

    public static Map<String, Object> doctor(Db db, Map<String, Object> r) {
        Map<String, Object> profile = db.one(
                "SELECT * FROM doctor_profiles WHERE user_id = ?", J.s(r.get("id")));
        return J.map(
                "id", J.s(r.get("id")),
                "name", J.s(r.get("name")),
                "email", J.s(r.get("email")),
                "initials", new Principal(r).initials,
                "avatarColor", J.s(r.get("avatar_color")),
                "specialization", profile == null ? "" : J.s(profile.get("specialization")),
                "hospital", profile == null ? "" : J.s(profile.get("hospital")),
                "department", profile == null ? "" : J.s(profile.get("department")),
                "verificationStatus", profile == null
                        ? "PENDING" : J.s(profile.get("verification_status")));
    }

    public static Map<String, Object> smallUser(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "name", J.s(r.get("name")),
                "email", J.s(r.get("email")),
                "initials", new Principal(r).initials,
                "avatarColor", J.s(r.get("avatar_color")));
    }

    public static Map<String, Object> grant(Db db, Map<String, Object> r) {
        String doctorId = J.s(r.get("doctor_id"));
        String patientId = J.s(r.get("patient_id"));
        Map<String, Object> doctor = doctorId.isEmpty() ? null
                : db.one("SELECT * FROM users WHERE id = ?", doctorId);
        Map<String, Object> patient = patientId.isEmpty() ? null
                : db.one("SELECT * FROM users WHERE id = ?", patientId);
        boolean effective = "ACTIVE".equals(J.s(r.get("status")));
        Object expires = r.get("expires_at");
        if (expires instanceof Timestamp t && !t.after(J.ts())) effective = false;
        return J.map(
                "id", J.s(r.get("id")),
                "patientId", patientId,
                "doctorId", doctorId,
                "doctor", doctor == null ? null : doctor(db, doctor),
                "patient", patient == null ? null : smallUser(patient),
                "scope", J.strings(r.get("scope")),
                "purpose", J.s(r.get("purpose")),
                "status", J.s(r.get("status")),
                "isEffective", effective,
                "grantedAt", J.iso(r.get("granted_at")),
                "expiresAt", J.iso(expires),
                "revokedAt", J.iso(r.get("revoked_at")),
                "createdAt", J.iso(r.get("created_at")));
    }

    public static Map<String, Object> record(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "category", J.s(r.get("category")),
                "title", J.s(r.get("title")),
                "summary", J.s(r.get("summary")),
                "payload", J.json(r.get("payload")),
                "sourceType", J.s(r.get("source_type")),
                "verificationStatus", J.s(r.get("verification_status")),
                "sourceDocumentId", J.sn(r.get("source_document_id")),
                "authorId", J.sn(r.get("author_id")),
                "recordedAt", J.iso(r.get("recorded_at")),
                "createdAt", J.iso(r.get("created_at")),
                "updatedAt", J.iso(r.get("updated_at")),
                "isAiGenerated", "AI_GENERATED".equals(J.s(r.get("source_type"))));
    }

    public static Map<String, Object> observation(Map<String, Object> r) {
        Object raw = r.get("value_numeric");
        Object value = J.num(raw);
        String display;
        if (raw == null) {
            String text = J.s(r.get("value_text"));
            display = text.isEmpty() ? "—" : text;
        } else {
            double number = ((Number) J.num(raw)).doubleValue();
            String rendered = number == Math.rint(number)
                    ? String.valueOf((long) number) : String.valueOf(number);
            display = (rendered + " " + J.s(r.get("unit"))).trim();
        }
        return J.map(
                "id", J.s(r.get("id")),
                "code", J.s(r.get("code")),
                "label", J.s(r.get("label")),
                "value", value,
                "valueText", J.s(r.get("value_text")),
                "displayValue", display,
                "unit", J.s(r.get("unit")),
                "referenceRange", J.s(r.get("reference_range")),
                "flag", J.s(r.get("flag")),
                "observedAt", J.iso(r.get("observed_at")),
                "sourceType", J.s(r.get("source_type")));
    }

    public static Map<String, Object> allergy(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "substance", J.s(r.get("substance")),
                "reaction", J.s(r.get("reaction")),
                "severity", J.s(r.get("severity")),
                "status", J.s(r.get("status")),
                "sourceType", J.s(r.get("source_type")),
                "reviewedAt", J.iso(r.get("reviewed_at")),
                "createdAt", J.iso(r.get("created_at")));
    }

    public static Map<String, Object> medication(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "name", J.s(r.get("name")),
                "dose", J.s(r.get("dose")),
                "frequency", J.s(r.get("frequency")),
                "route", J.s(r.get("route")),
                "status", J.s(r.get("status")),
                "startedAt", J.iso(r.get("started_at")),
                "endedAt", J.iso(r.get("ended_at")),
                "sourceType", J.s(r.get("source_type")));
    }

    public static Map<String, Object> extraction(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "fieldName", J.s(r.get("field_name")),
                "label", J.s(r.get("label")),
                "value", J.s(r.get("value")),
                "confidence", J.num(r.get("confidence")),
                "reviewStatus", J.s(r.get("review_status")),
                "evidence", J.s(r.get("evidence")));
    }

    public static Map<String, Object> document(Map<String, Object> r, List<Map<String, Object>> extractions) {
        Map<String, Object> out = J.map(
                "id", J.s(r.get("id")),
                "name", J.s(r.get("name")),
                "mimeType", J.s(r.get("mime_type")),
                "sizeBytes", J.num(r.get("size_bytes")),
                "category", J.s(r.get("category")),
                "processingStatus", J.s(r.get("processing_status")),
                "processingError", J.s(r.get("processing_error")),
                "pageCount", J.num(r.get("page_count")),
                "createdAt", J.iso(r.get("created_at")),
                "processedAt", J.iso(r.get("processed_at")),
                "hasExtractedText", !J.s(r.get("extracted_text")).isBlank());
        if (extractions != null) {
            List<Map<String, Object>> items = new ArrayList<>();
            for (Map<String, Object> row : extractions) items.add(extraction(row));
            out.put("extractions", items);
        }
        return out;
    }

    public static Map<String, Object> timeline(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "eventType", J.s(r.get("event_type")),
                "title", J.s(r.get("title")),
                "description", J.s(r.get("description")),
                "occurredAt", J.iso(r.get("occurred_at")),
                "sourceType", J.s(r.get("source_type")),
                "sourceId", J.sn(r.get("source_id")));
    }

    public static Map<String, Object> conversation(Db db, Map<String, Object> r, Principal viewer) {
        String otherId = "PATIENT".equals(viewer.role)
                ? J.s(r.get("doctor_id")) : J.s(r.get("patient_id"));
        Map<String, Object> other = otherId.isEmpty() ? null
                : db.one("SELECT * FROM users WHERE id = ?", otherId);
        Map<String, Object> last = db.one("SELECT * FROM messages WHERE conversation_id = ? "
                + "ORDER BY created_at DESC LIMIT 1", J.s(r.get("id")));
        long unread = db.count("SELECT COUNT(*) FROM messages WHERE conversation_id = ? "
                        + "AND read_at IS NULL AND (sender_id IS NULL OR sender_id <> ?)",
                J.s(r.get("id")), viewer.id);
        Map<String, Object> counterpart = null;
        if (other != null) {
            Map<String, Object> profile = db.one(
                    "SELECT specialization FROM doctor_profiles WHERE user_id = ?", otherId);
            counterpart = J.map(
                    "id", J.s(other.get("id")),
                    "name", J.s(other.get("name")),
                    "initials", new Principal(other).initials,
                    "avatarColor", J.s(other.get("avatar_color")),
                    "specialization", profile == null ? "" : J.s(profile.get("specialization")));
        }
        return J.map(
                "id", J.s(r.get("id")),
                "title", J.s(r.get("title")).isEmpty()
                        ? (other == null ? "Conversation" : J.s(other.get("name")))
                        : J.s(r.get("title")),
                "channel", J.s(r.get("channel")),
                "counterpart", counterpart,
                "lastMessage", last == null ? "" : J.s(last.get("body")).substring(
                        0, Math.min(160, J.s(last.get("body")).length())),
                "lastMessageAt", last == null ? null : J.iso(last.get("created_at")),
                "unread", unread,
                "updatedAt", J.iso(r.get("updated_at")));
    }

    public static Map<String, Object> message(Db db, Map<String, Object> r) {
        String senderId = J.s(r.get("sender_id"));
        String senderName = "MedTwin AI";
        if (!senderId.isEmpty()) {
            Map<String, Object> sender = db.one("SELECT name FROM users WHERE id = ?", senderId);
            senderName = sender == null ? "" : J.s(sender.get("name"));
        }
        return J.map(
                "id", J.s(r.get("id")),
                "role", J.s(r.get("role")),
                "body", J.s(r.get("body")),
                "senderId", J.sn(r.get("sender_id")),
                "senderName", senderName,
                "createdAt", J.iso(r.get("created_at")),
                "readAt", J.iso(r.get("read_at")));
    }

    public static Map<String, Object> appointment(Db db, Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "patientId", J.s(r.get("patient_id")),
                "doctorId", J.s(r.get("doctor_id")),
                "patientName", nameOf(db, J.s(r.get("patient_id"))),
                "doctorName", nameOf(db, J.s(r.get("doctor_id"))),
                "scheduledAt", J.iso(r.get("scheduled_at")),
                "durationMin", J.num(r.get("duration_min")),
                "timezone", J.s(r.get("timezone")),
                "reason", J.s(r.get("reason")),
                "status", J.s(r.get("status")),
                "notes", J.s(r.get("notes")),
                "createdAt", J.iso(r.get("created_at")));
    }

    private static String nameOf(Db db, String id) {
        if (id.isEmpty()) return "";
        Map<String, Object> row = db.one("SELECT name FROM users WHERE id = ?", id);
        return row == null ? "" : J.s(row.get("name"));
    }

    public static Map<String, Object> notification(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "type", J.s(r.get("type")),
                "title", J.s(r.get("title")),
                "body", J.s(r.get("body")),
                "link", J.s(r.get("link")),
                "isRead", J.bool(r.get("is_read")),
                "createdAt", J.iso(r.get("created_at")));
    }

    public static Map<String, Object> source(Db db, Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "title", J.s(r.get("title")),
                "publisher", J.s(r.get("publisher")),
                "version", J.s(r.get("version")),
                "sourceUrl", J.s(r.get("source_url")),
                "category", J.s(r.get("category")),
                "licenseStatus", J.s(r.get("license_status")),
                "reviewStatus", J.s(r.get("review_status")),
                "ingestedAt", J.iso(r.get("ingested_at")),
                "chunkCount", db.count("SELECT COUNT(*) FROM knowledge_chunks WHERE source_id = ?",
                        J.s(r.get("id"))),
                "createdAt", J.iso(r.get("created_at")));
    }

    public static Map<String, Object> audit(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "actorId", J.sn(r.get("actor_id")),
                "actorEmail", J.s(r.get("actor_email")),
                "action", J.s(r.get("action")),
                "resourceType", J.s(r.get("resource_type")),
                "resourceId", J.s(r.get("resource_id")),
                "outcome", J.s(r.get("outcome")),
                "ipAddress", J.s(r.get("ip_address")),
                "traceId", J.s(r.get("trace_id")),
                "metadata", J.json(r.get("metadata")),
                "createdAt", J.iso(r.get("created_at")));
    }

    public static Map<String, Object> flag(Map<String, Object> r) {
        return J.map(
                "id", J.s(r.get("id")),
                "key", J.s(r.get("flag_key")),
                "label", J.s(r.get("label")),
                "description", J.s(r.get("description")),
                "isEnabled", J.bool(r.get("is_enabled")),
                "status", J.s(r.get("status")),
                "updatedAt", J.iso(r.get("updated_at")));
    }
}
