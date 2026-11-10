package com.medtwin.core;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.sql.Date;
import java.sql.Timestamp;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

/** Small, explicit helpers shared by every controller. The API contract is hand-written camelCase. */
public final class J {
    public static final ObjectMapper JSON = new ObjectMapper();

    private J() {
    }

    public static Map<String, Object> map(Object... kv) {
        LinkedHashMap<String, Object> out = new LinkedHashMap<>();
        for (int i = 0; i + 1 < kv.length; i += 2) {
            out.put(String.valueOf(kv[i]), kv[i + 1]);
        }
        return out;
    }

    public static String s(Object value) {
        return value == null ? "" : String.valueOf(value);
    }

    public static String sn(Object value) {
        return value == null ? null : String.valueOf(value);
    }

    public static Object g(Map<String, Object> body, String key) {
        return body == null ? null : body.get(key);
    }

    public static String gs(Map<String, Object> body, String key) {
        return s(g(body, key));
    }

    public static String gsn(Map<String, Object> body, String key) {
        return sn(g(body, key));
    }

    @SuppressWarnings("unchecked")
    public static Map<String, Object> gm(Map<String, Object> body, String key) {
        Object value = g(body, key);
        return value instanceof Map<?, ?> ? (Map<String, Object>) value : new LinkedHashMap<>();
    }

    public static int gi(Map<String, Object> body, String key, int fallback) {
        Object value = g(body, key);
        if (value == null || s(value).isBlank()) return fallback;
        try {
            return (int) Double.parseDouble(s(value));
        } catch (NumberFormatException exc) {
            return fallback;
        }
    }

    public static boolean bool(Object value) {
        if (value == null) return false;
        if (value instanceof Boolean b) return b;
        if (value instanceof Number n) return n.intValue() != 0;
        String text = String.valueOf(value);
        return text.equals("1") || text.equalsIgnoreCase("true");
    }

    public static Object num(Object value) {
        if (value == null) return null;
        if (value instanceof BigDecimal d) {
            double x = d.doubleValue();
            return x == Math.rint(x) && Math.abs(x) < 1e15 ? (long) x : x;
        }
        if (value instanceof Number n) return n;
        try {
            return Double.valueOf(String.valueOf(value));
        } catch (NumberFormatException exc) {
            return null;
        }
    }

    public static Object json(Object value) {
        if (value == null) return new LinkedHashMap<String, Object>();
        String text = value instanceof byte[] bytes
                ? new String(bytes, StandardCharsets.UTF_8)
                : String.valueOf(value);
        if (text.isBlank()) return new LinkedHashMap<String, Object>();
        try {
            return JSON.readValue(text, Object.class);
        } catch (Exception exc) {
            return new LinkedHashMap<String, Object>();
        }
    }

    public static List<String> strings(Object value) {
        if (value == null) return List.of();
        String text = value instanceof byte[] bytes
                ? new String(bytes, StandardCharsets.UTF_8)
                : String.valueOf(value);
        try {
            Object parsed = JSON.readValue(text, Object.class);
            if (parsed instanceof List<?> items) {
                return items.stream().map(J::s).collect(Collectors.toList());
            }
        } catch (Exception ignored) {
            // fall through to comma-separated form
        }
        return Arrays.stream(text.split(","))
                .map(String::trim)
                .filter(item -> !item.isEmpty())
                .collect(Collectors.toList());
    }

    public static String toJson(Object value) {
        try {
            return JSON.writeValueAsString(value == null ? new LinkedHashMap<>() : value);
        } catch (Exception exc) {
            return "{}";
        }
    }

    /** Matches Django's iso(): UTC datetimes are rendered with an explicit +00:00 offset. */
    public static String iso(Object value) {
        if (value == null) return null;
        if (value instanceof Timestamp t) return t.toLocalDateTime() + "+00:00";
        if (value instanceof Date d) return d.toLocalDate().toString();
        if (value instanceof LocalDateTime l) return l + "+00:00";
        if (value instanceof LocalDate l) return l.toString();
        if (value instanceof String text) return text.isEmpty() ? null : text;
        return String.valueOf(value);
    }

    public static String nowIso() {
        return LocalDateTime.now(ZoneOffset.UTC) + "+00:00";
    }

    public static Timestamp ts() {
        return Timestamp.valueOf(LocalDateTime.now(ZoneOffset.UTC));
    }

    public static Timestamp plusDays(int days) {
        return Timestamp.valueOf(LocalDateTime.now(ZoneOffset.UTC).plusDays(days));
    }

    public static String uuid() {
        return UUID.randomUUID().toString();
    }

    public static String trace() {
        return UUID.randomUUID().toString().replace("-", "").substring(0, 32);
    }

    public static List<Map<String, Object>> list() {
        return new ArrayList<>();
    }
}
