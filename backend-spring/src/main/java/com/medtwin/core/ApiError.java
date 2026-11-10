package com.medtwin.core;

import java.util.Map;

/** DRF-compatible error body: either {"error": ...} or {"detail": ...}. */
public class ApiError extends RuntimeException {
    public final int status;
    public final Map<String, Object> body;

    public ApiError(int status, String message) {
        this(status, "error", message);
    }

    public ApiError(int status, String key, String message) {
        super(message);
        this.status = status;
        this.body = J.map(key, message);
    }

    public static ApiError bad(String message) {
        return new ApiError(400, message);
    }

    public static ApiError forbidden() {
        return new ApiError(403, "detail", "Your role does not allow this action.");
    }

    public static ApiError unauthenticated() {
        return new ApiError(403, "detail", "Authentication credentials were not provided.");
    }

    public static ApiError notFound(String message) {
        return new ApiError(404, "detail", message);
    }

    public static ApiError conflict(String message) {
        return new ApiError(409, message);
    }

    public static ApiError unavailable(String message) {
        return new ApiError(503, message);
    }
}
