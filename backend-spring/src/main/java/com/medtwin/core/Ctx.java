package com.medtwin.core;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

public final class Ctx {
    public static final String PRINCIPAL = "medtwin.principal";

    private Ctx() {
    }

    public static HttpServletRequest req() {
        return ((ServletRequestAttributes) RequestContextHolder.currentRequestAttributes()).getRequest();
    }

    public static Principal user() {
        Principal value = (Principal) req().getAttribute(PRINCIPAL);
        if (value == null) throw ApiError.unauthenticated();
        return value;
    }

    public static String path() {
        HttpServletRequest request = req();
        String uri = request.getRequestURI();
        String context = request.getContextPath();
        return uri.startsWith(context) ? uri.substring(context.length()) : uri;
    }
}
