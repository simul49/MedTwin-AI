package com.medtwin.core;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.stereotype.Service;

/** Audit writes never break the request, matching the Django helper's contract. */
@Service
public class Audit {
    private final Db db;

    public Audit(Db db) {
        this.db = db;
    }

    public void log(String action) {
        log(action, "", "", "SUCCESS", null);
    }

    public void log(String action, String resourceType, String resourceId,
                    String outcome, Object metadata) {
        try {
            HttpServletRequest request = Ctx.req();
            Principal user = (Principal) request.getAttribute(Ctx.PRINCIPAL);
            String forwarded = request.getHeader("X-Forwarded-For");
            String ip = forwarded != null && !forwarded.isBlank()
                    ? forwarded.split(",")[0].trim()
                    : request.getRemoteAddr();
            String agent = request.getHeader("User-Agent");
            db.exec("INSERT INTO audit_logs (id, actor_id, actor_email, action, resource_type, "
                            + "resource_id, outcome, ip_address, user_agent, trace_id, metadata, created_at) "
                            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    J.uuid(),
                    user == null ? null : user.id,
                    user == null ? "" : user.email,
                    action,
                    resourceType,
                    resourceId,
                    outcome,
                    ip == null ? "" : ip,
                    agent == null ? "" : agent.substring(0, Math.min(255, agent.length())),
                    J.trace(),
                    metadata == null ? null : J.toJson(metadata),
                    J.ts());
        } catch (Exception ignored) {
            // auditing must not break a request
        }
    }
}
