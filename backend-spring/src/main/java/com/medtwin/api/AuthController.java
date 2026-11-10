package com.medtwin.api;

import com.medtwin.config.AppProps;
import com.medtwin.core.*;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Pattern;

@RestController
public class AuthController {
    private static final Pattern EMAIL = Pattern.compile("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$");
    private static final Pattern PASSWORD = Pattern.compile("^(?=.*[A-Za-z])(?=.*\\d).{8,}$");
    private static final List<String> COLORS = List.of(
            "#2563eb", "#0ea5e9", "#0f766e", "#7c3aed", "#c2410c", "#be123c", "#15803d");
    private static final Map<String, Attempt> ATTEMPTS = new ConcurrentHashMap<>();

    private final Db db;
    private final Sessions sessions;
    private final AuthInterceptor auth;
    private final Audit audit;
    private final Access access;
    private final AppProps props;

    public AuthController(Db db, Sessions sessions, AuthInterceptor auth, Audit audit,
                          Access access, AppProps props) {
        this.db = db;
        this.sessions = sessions;
        this.auth = auth;
        this.audit = audit;
        this.access = access;
        this.props = props;
    }

    @GetMapping("/auth/csrf/")
    public Map<String, Object> csrf(HttpServletResponse response) {
        return J.map("csrfToken", auth.issueCsrf(response));
    }

    @PostMapping("/auth/register/")
    public ResponseEntity<Object> register(@RequestBody(required = false) Map<String, Object> body,
                                           HttpServletResponse response) {
        String name = J.gs(body, "name").trim();
        String email = J.gs(body, "email").trim().toLowerCase();
        String password = J.gs(body, "password");
        String role = J.gs(body, "role").isEmpty() ? "PATIENT" : J.gs(body, "role").toUpperCase();
        Map<String, Object> errors = new LinkedHashMap<>();
        if (name.length() < 2) errors.put("name", "Enter your full name.");
        if (!EMAIL.matcher(email).matches()) errors.put("email", "Enter a valid email address.");
        else if (db.one("SELECT id FROM users WHERE email = ?", email) != null) {
            errors.put("email", "An account with this email already exists.");
        }
        if (!PASSWORD.matcher(password).matches()) {
            errors.put("password", "Use at least 8 characters, including a letter and a number.");
        }
        if (!role.equals("PATIENT") && !role.equals("DOCTOR")) {
            errors.put("role", "Choose Patient or Doctor.");
        }
        if (role.equals("DOCTOR") && J.gs(body, "specialization").trim().isEmpty()) {
            errors.put("specialization", "Add your specialization so patients can identify you.");
        }
        if (!J.bool(J.g(body, "acknowledge"))) {
            errors.put("acknowledge", "Please confirm the medical disclaimer to continue.");
        }
        if (!errors.isEmpty()) {
            ApiError error = ApiError.bad("Please correct the highlighted fields.");
            error.body.put("fields", errors);
            throw error;
        }

        String id = J.uuid();
        String language = J.gs(body, "language").isEmpty()
                ? "en" : J.gs(body, "language").toLowerCase().substring(0, 2);
        if (!language.equals("zh")) language = "en";
        db.exec("INSERT INTO users (id, name, email, password_hash, role, phone, avatar_color, "
                        + "language, is_active, is_verified, created_at, updated_at) "
                        + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, ?, ?)",
                id, name, email, Passwords.encode(password), role,
                nullIfBlank(J.gs(body, "phone").trim()), avatarColor(email), language,
                J.ts(), J.ts());
        if (role.equals("PATIENT")) {
            db.exec("INSERT INTO patient_profiles (id, user_id, date_of_birth, gender, "
                            + "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    J.uuid(), id, nullIfBlank(first(body, "date_of_birth", "dateOfBirth")),
                    enumOr(first(body, "gender", "gender"), "UNDISCLOSED",
                            Set.of("FEMALE", "MALE", "NON_BINARY", "UNDISCLOSED")),
                    J.ts(), J.ts());
        } else {
            db.exec("INSERT INTO doctor_profiles (id, user_id, specialization, license_number, "
                            + "hospital, department, verification_status, created_at, updated_at) "
                            + "VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)",
                    J.uuid(), id, J.gs(body, "specialization").trim(),
                    first(body, "license_number", "licenseNumber"),
                    J.gs(body, "hospital").trim(), J.gs(body, "department").trim(),
                    J.ts(), J.ts());
        }
        Ctx.req().setAttribute(Ctx.PRINCIPAL, new Principal(db.require("SELECT * FROM users WHERE id = ?", id)));
        audit.log("REGISTER", "user", id, "SUCCESS", J.map("role", role));
        sessions.start(id, response);
        return ResponseEntity.status(201).body(Views.user(db, db.require("SELECT * FROM users WHERE id = ?", id), true));
    }

    @PostMapping("/auth/login/")
    public Map<String, Object> login(@RequestBody(required = false) Map<String, Object> body,
                                     HttpServletRequest request, HttpServletResponse response) {
        String email = J.gs(body, "email").trim().toLowerCase();
        String password = J.gs(body, "password");
        String key = email + "|" + request.getRemoteAddr();
        Attempt attempt = ATTEMPTS.get(key);
        if (attempt != null && attempt.blockedUntil > System.currentTimeMillis()) {
            audit.log("LOGIN", "session", "", "DENIED",
                    J.map("reason", "rate_limited", "email", email));
            throw new ApiError(429, "Too many attempts. Please try again later.");
        }

        Map<String, Object> user = db.one("SELECT * FROM users WHERE email = ?", email);
        if (user == null || !Passwords.matches(password, J.s(user.get("password_hash")))
                || !J.bool(user.get("is_active"))) {
            Attempt current = ATTEMPTS.computeIfAbsent(key, ignored -> new Attempt());
            current.failures++;
            if (current.failures >= 8) {
                current.blockedUntil = System.currentTimeMillis() + 15L * 60 * 1000;
                current.failures = 0;
            }
            audit.log("LOGIN", "session", "", "DENIED", J.map("email", email));
            throw new ApiError(401, "Email or password is incorrect.");
        }
        ATTEMPTS.remove(key);

        String id = J.s(user.get("id"));
        db.exec("UPDATE users SET last_login_at = ? WHERE id = ?", J.ts(), id);
        sessions.start(id, response);
        Ctx.req().setAttribute(Ctx.PRINCIPAL, new Principal(db.require("SELECT * FROM users WHERE id = ?", id)));
        audit.log("LOGIN", "session", id, "SUCCESS", null);
        return Views.user(db, db.require("SELECT * FROM users WHERE id = ?", id), true);
    }

    @PostMapping("/auth/logout/")
    public Map<String, Object> logout(HttpServletRequest request, HttpServletResponse response) {
        audit.log("LOGOUT", "session", "", "SUCCESS", null);
        sessions.end(request, response);
        return J.map("ok", true);
    }

    @PostMapping("/auth/password/change/")
    public Map<String, Object> changePassword(@RequestBody(required = false) Map<String, Object> body) {
        Principal user = Ctx.user();
        Map<String, Object> row = db.require("SELECT * FROM users WHERE id = ?", user.id);
        if (!Passwords.matches(J.gs(body, "currentPassword"), J.s(row.get("password_hash")))) {
            throw ApiError.bad("Current password is incorrect.");
        }
        String next = J.gs(body, "newPassword");
        if (!PASSWORD.matcher(next).matches()) {
            throw ApiError.bad("Use at least 8 characters, including a letter and a number.");
        }
        db.exec("UPDATE users SET password_hash = ? WHERE id = ?", Passwords.encode(next), user.id);
        audit.log("PASSWORD_CHANGE", "user", user.id, "SUCCESS", null);
        return J.map("ok", true);
    }

    @PostMapping("/auth/password/forgot/")
    public Map<String, Object> forgot(@RequestBody(required = false) Map<String, Object> body) {
        String email = J.gs(body, "email").trim().toLowerCase();
        Map<String, Object> user = db.one("SELECT * FROM users WHERE email = ?", email);
        if (user == null) return J.map("ok", true);
        byte[] bytes = new byte[32];
        new SecureRandom().nextBytes(bytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
        db.exec("INSERT INTO password_reset_tokens (id, user_id, token_hash, expires_at, created_at) "
                        + "VALUES (?, ?, ?, ?, ?)",
                J.uuid(), J.s(user.get("id")), sha256(token),
                Timestamp.valueOf(LocalDateTime.now(ZoneOffset.UTC).plusHours(1)), J.ts());
        audit.log("PASSWORD_RESET_REQUEST", "user", J.s(user.get("id")), "SUCCESS", null);
        return J.map("ok", true, "devToken", token);
    }

    @PostMapping("/auth/password/reset/")
    public Map<String, Object> reset(@RequestBody(required = false) Map<String, Object> body) {
        String token = J.gs(body, "token");
        Map<String, Object> row = db.one(
                "SELECT * FROM password_reset_tokens WHERE token_hash = ?", sha256(token));
        if (row == null || row.get("used_at") != null) {
            throw ApiError.bad("This reset link is invalid or expired.");
        }
        Object expires = row.get("expires_at");
        if (expires instanceof Timestamp t && !t.after(J.ts())) {
            throw ApiError.bad("This reset link is invalid or expired.");
        }
        String password = J.gs(body, "password");
        if (!PASSWORD.matcher(password).matches()) {
            throw ApiError.bad("Use at least 8 characters, including a letter and a number.");
        }
        String userId = J.s(row.get("user_id"));
        db.exec("UPDATE users SET password_hash = ? WHERE id = ?", Passwords.encode(password), userId);
        db.exec("UPDATE password_reset_tokens SET used_at = ? WHERE id = ?", J.ts(), J.s(row.get("id")));
        audit.log("PASSWORD_RESET", "user", userId, "SUCCESS", null);
        return J.map("ok", true);
    }

    @GetMapping("/me/")
    public Map<String, Object> me() {
        return Views.user(db, db.require("SELECT * FROM users WHERE id = ?", Ctx.user().id), true);
    }

    @PatchMapping("/me/")
    public Map<String, Object> updateMe(@RequestBody(required = false) Map<String, Object> body) {
        Principal user = Ctx.user();
        List<String> changed = new ArrayList<>();
        List<String> sets = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        for (String field : List.of("name", "phone", "language")) {
            if (J.g(body, field) != null) {
                String value = J.gs(body, field);
                if (field.equals("language") && !value.equals("zh")) value = "en";
                sets.add(field + " = ?");
                args.add(value);
                changed.add(field);
            }
        }
        if (!sets.isEmpty()) {
            args.add(user.id);
            db.exec("UPDATE users SET " + String.join(", ", sets) + " WHERE id = ?", args.toArray());
        }

        Map<String, Object> patient = J.gm(body, "patientProfile");
        if (user.role.equals("PATIENT") && !patient.isEmpty()) {
            Map<String, Object> profile = db.one(
                    "SELECT id FROM patient_profiles WHERE user_id = ?", user.id);
            if (profile == null) {
                db.exec("INSERT INTO patient_profiles (id, user_id, gender, created_at, updated_at) "
                                + "VALUES (?, ?, 'UNDISCLOSED', ?, ?)",
                        J.uuid(), user.id, J.ts(), J.ts());
                profile = db.one("SELECT id FROM patient_profiles WHERE user_id = ?", user.id);
            }
            applyProfileUpdate("patient_profiles", J.s(profile.get("id")), patient,
                    columns("date_of_birth", "date_of_birth", "dateOfBirth", "date_of_birth",
                            "gender", "gender", "blood_type", "blood_type", "bloodType", "blood_type",
                            "city", "city", "emergency_contact", "emergency_contact",
                            "emergencyContact", "emergency_contact", "summary", "summary",
                            "height_cm", "height_cm", "heightCm", "height_cm",
                            "weight_kg", "weight_kg", "weightKg", "weight_kg"), changed);
        }

        Map<String, Object> doctor = J.gm(body, "doctorProfile");
        if (user.role.equals("DOCTOR") && !doctor.isEmpty()) {
            Map<String, Object> profile = db.one(
                    "SELECT id FROM doctor_profiles WHERE user_id = ?", user.id);
            if (profile == null) {
                db.exec("INSERT INTO doctor_profiles (id, user_id, verification_status, "
                                + "created_at, updated_at) VALUES (?, ?, 'PENDING', ?, ?)",
                        J.uuid(), user.id, J.ts(), J.ts());
                profile = db.one("SELECT id FROM doctor_profiles WHERE user_id = ?", user.id);
            }
            applyProfileUpdate("doctor_profiles", J.s(profile.get("id")), doctor,
                    columns("specialization", "specialization", "license_number", "license_number",
                            "licenseNumber", "license_number", "hospital", "hospital",
                            "department", "department", "bio", "bio"), changed);
        }

        audit.log("PROFILE_UPDATE", "user", user.id, "SUCCESS", J.map("fields", changed));
        return Views.user(db, db.require("SELECT * FROM users WHERE id = ?", user.id), true);
    }

    @GetMapping("/doctors/")
    public Map<String, Object> doctors() {
        access.require("PATIENT", "ADMIN");
        List<Map<String, Object>> results = new ArrayList<>();
        for (Map<String, Object> row : db.list(
                "SELECT * FROM users WHERE role = 'DOCTOR' AND is_active = 1 ORDER BY created_at DESC")) {
            results.add(Views.doctor(db, row));
        }
        return J.map("results", results);
    }

    private void applyProfileUpdate(String table, String id, Map<String, Object> payload,
                                    Map<String, String> columns, List<String> changed) {
        List<String> sets = new ArrayList<>();
        List<Object> args = new ArrayList<>();
        for (Map.Entry<String, String> entry : columns.entrySet()) {
            if (!payload.containsKey(entry.getKey()) || sets.contains(entry.getValue() + " = ?")) continue;
            Object value = payload.get(entry.getKey());
            sets.add(entry.getValue() + " = ?");
            args.add(value == null || J.s(value).isBlank() ? null : J.s(value));
            changed.add("profile." + entry.getValue());
        }
        if (sets.isEmpty()) return;
        args.add(id);
        db.exec("UPDATE " + table + " SET " + String.join(", ", sets) + " WHERE id = ?",
                args.toArray());
    }

    private static Map<String, String> columns(String... pairs) {
        Map<String, String> out = new LinkedHashMap<>();
        for (int i = 0; i + 1 < pairs.length; i += 2) out.put(pairs[i], pairs[i + 1]);
        return out;
    }

    private static String first(Map<String, Object> body, String a, String b) {
        String value = J.gs(body, a);
        return value.isEmpty() ? J.gs(body, b) : value;
    }

    private static String enumOr(String value, String fallback, Set<String> allowed) {
        String upper = value.toUpperCase();
        return allowed.contains(upper) ? upper : fallback;
    }

    private static String nullIfBlank(String value) {
        return value == null || value.isBlank() ? null : value;
    }

    private static String avatarColor(String seed) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(seed.getBytes(StandardCharsets.UTF_8));
            return COLORS.get((digest[0] & 0xff) % COLORS.size());
        } catch (Exception exc) {
            return COLORS.get(0);
        }
    }

    private static String sha256(String value) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256")
                    .digest(value.getBytes(StandardCharsets.UTF_8));
            StringBuilder out = new StringBuilder();
            for (byte b : digest) out.append(String.format("%02x", b));
            return out.toString();
        } catch (Exception exc) {
            return "";
        }
    }

    private static final class Attempt {
        int failures;
        long blockedUntil;
    }
}
