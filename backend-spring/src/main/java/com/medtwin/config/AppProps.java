package com.medtwin.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "medtwin")
public class AppProps {
    private String aiServiceUrl = "http://127.0.0.1:8002";
    private String aiSharedSecret = "";
    private int sessionHours = 8;
    private String uploadDir = "../backend/var/documents";
    private String csrfCookie = "medtwin_csrf";
    private String sessionCookie = "medtwin_session";
    private String corsOrigins = "http://localhost:5173,http://127.0.0.1:5173";

    public String getAiServiceUrl() { return aiServiceUrl; }
    public void setAiServiceUrl(String value) { this.aiServiceUrl = value; }
    public String getAiSharedSecret() { return aiSharedSecret; }
    public void setAiSharedSecret(String value) { this.aiSharedSecret = value; }
    public int getSessionHours() { return sessionHours; }
    public void setSessionHours(int value) { this.sessionHours = value; }
    public String getUploadDir() { return uploadDir; }
    public void setUploadDir(String value) { this.uploadDir = value; }
    public String getCsrfCookie() { return csrfCookie; }
    public void setCsrfCookie(String value) { this.csrfCookie = value; }
    public String getSessionCookie() { return sessionCookie; }
    public void setSessionCookie(String value) { this.sessionCookie = value; }
    public String getCorsOrigins() { return corsOrigins; }
    public void setCorsOrigins(String value) { this.corsOrigins = value; }
}
