package com.medtwin.core;

import com.medtwin.config.AppProps;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseCookie;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.sql.Timestamp;
import java.time.Duration;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;

/**
 * Session store. Reuses the existing `django_session` table, but stores plain
 * JSON instead of Django's signed payload: Spring is now the only session owner.
 */
@Service
public class Sessions {
    private static final SecureRandom RANDOM = new SecureRandom();

    private final Db db;
    private final AppProps props;

    public Sessions(Db db, AppProps props) {
        this.db = db;
        this.props = props;
    }

    public Principal resolve(HttpServletRequest request) {
        String key = cookieValue(request, props.getSessionCookie());
        if (key == null || key.length() > 40) return null;
        Map<String, Object> row = db.one(
                "SELECT session_data, expire_date FROM django_session WHERE session_key = ?", key);
        if (row == null) return null;
        Object expiry = row.get("expire_date");
        if (expiry instanceof Timestamp t && !t.after(J.ts())) return null;
        try {
            Map<?, ?> payload = J.JSON.readValue(J.s(row.get("session_data")), Map.class);
            String userId = J.s(payload.get("userId"));
            if (userId.isEmpty()) return null;
            Map<String, Object> user = db.one(
                    "SELECT * FROM users WHERE id = ? AND is_active = 1", userId);
            return user == null ? null : new Principal(user);
        } catch (Exception exc) {
            return null;
        }
    }

    public void start(String userId, HttpServletResponse response) {
        byte[] bytes = new byte[20];
        RANDOM.nextBytes(bytes);
        StringBuilder key = new StringBuilder();
        for (byte b : bytes) key.append(String.format("%02x", b));
        Timestamp expiry = Timestamp.valueOf(
                LocalDateTime.now(ZoneOffset.UTC).plusHours(props.getSessionHours()));
        db.exec("INSERT INTO django_session (session_key, session_data, expire_date) VALUES (?, ?, ?)",
                key.toString(), J.toJson(J.map("userId", userId)), expiry);
        setCookie(response, props.getSessionCookie(), key.toString(), true,
                Duration.ofHours(props.getSessionHours()));
    }

    public void end(HttpServletRequest request, HttpServletResponse response) {
        String key = cookieValue(request, props.getSessionCookie());
        if (key != null) db.exec("DELETE FROM django_session WHERE session_key = ?", key);
        setCookie(response, props.getSessionCookie(), "", true, Duration.ZERO);
    }

    public void setCsrf(HttpServletResponse response, String token) {
        setCookie(response, props.getCsrfCookie(), token, false,
                Duration.ofHours(props.getSessionHours()));
    }

    public void setCookie(HttpServletResponse response, String name, String value,
                          boolean httpOnly, Duration age) {
        ResponseCookie cookie = ResponseCookie.from(name, value)
                .httpOnly(httpOnly)
                .path("/")
                .sameSite("Lax")
                .maxAge(age)
                .build();
        response.addHeader(HttpHeaders.SET_COOKIE, cookie.toString());
    }

    public String csrfFromRequest(HttpServletRequest request) {
        return cookieValue(request, props.getCsrfCookie());
    }

    public static String cookieValue(HttpServletRequest request, String name) {
        Cookie[] cookies = request.getCookies();
        if (cookies == null) return null;
        for (Cookie cookie : cookies) {
            if (cookie.getName().equals(name)) return cookie.getValue();
        }
        return null;
    }
}
