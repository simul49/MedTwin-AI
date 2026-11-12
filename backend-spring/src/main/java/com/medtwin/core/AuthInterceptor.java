package com.medtwin.core;

import com.medtwin.config.AppProps;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import java.security.MessageDigest;
import java.time.Duration;
import java.util.Set;

/** Session authentication + CSRF, mirroring DRF SessionAuthentication behaviour. */
@Component
public class AuthInterceptor implements HandlerInterceptor {
    private static final Set<String> PUBLIC = Set.of(
            "/health/", "/auth/csrf/", "/auth/login/", "/auth/register/",
            "/auth/password/forgot/", "/auth/password/reset/", "/ai/public-chat/");

    private final Sessions sessions;
    private final AppProps props;

    public AuthInterceptor(Sessions sessions, AppProps props) {
        this.sessions = sessions;
        this.props = props;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response,
                             Object handler) {
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) return true;

        String path = Ctx.path();
        // Public endpoints are CSRF-exempt, matching DRF's AllowAny views.
        if (PUBLIC.contains(path)) return true;

        boolean unsafe = !"GET".equalsIgnoreCase(request.getMethod())
                && !"HEAD".equalsIgnoreCase(request.getMethod());

        if (unsafe) {
            String expected = sessions.csrfFromRequest(request);
            String provided = request.getHeader("X-CSRFToken");
            if (expected == null || provided == null
                    || !MessageDigest.isEqual(expected.getBytes(), provided.getBytes())) {
                throw new ApiError(403, "detail", "CSRF Failed: token missing or incorrect.");
            }
        }

        Principal principal = sessions.resolve(request);
        if (principal == null) throw ApiError.unauthenticated();
        request.setAttribute(Ctx.PRINCIPAL, principal);
        return true;
    }

    public String issueCsrf(HttpServletResponse response) {
        byte[] bytes = new byte[24];
        new java.security.SecureRandom().nextBytes(bytes);
        StringBuilder token = new StringBuilder();
        for (byte b : bytes) token.append(String.format("%02x", b));
        String value = token.toString();
        sessions.setCookie(response, props.getCsrfCookie(), value, false,
                Duration.ofHours(props.getSessionHours()));
        return value;
    }
}
