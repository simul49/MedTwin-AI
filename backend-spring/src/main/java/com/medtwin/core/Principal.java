package com.medtwin.core;

import java.util.Map;

/** The authenticated user attached to the request by AuthInterceptor. */
public final class Principal {
    public final String id;
    public final String name;
    public final String email;
    public final String role;
    public final String language;
    public final String avatarColor;
    public final String initials;
    public final String passwordHash;
    public final boolean active;
    public final boolean verified;

    public Principal(Map<String, Object> row) {
        this.id = J.s(row.get("id"));
        this.name = J.s(row.get("name"));
        this.email = J.s(row.get("email"));
        this.role = J.s(row.get("role"));
        this.language = J.s(row.get("language"));
        this.avatarColor = J.s(row.get("avatar_color"));
        this.passwordHash = J.s(row.get("password_hash"));
        this.active = J.bool(row.get("is_active"));
        this.verified = J.bool(row.get("is_verified"));
        this.initials = initialsOf(this.name, this.email);
    }

    private static String initialsOf(String name, String email) {
        String[] parts = name.trim().split("\\s+");
        StringBuilder out = new StringBuilder();
        int used = 0;
        for (String part : parts) {
            if (part.isEmpty() || used == 2) continue;
            out.append(part.charAt(0));
            used++;
        }
        if (used == 0) {
            String fallback = email.isEmpty() ? "?" : email;
            return fallback.substring(0, Math.min(2, fallback.length())).toUpperCase();
        }
        return out.toString().toUpperCase();
    }
}
