package com.medtwin.core;

import com.medtwin.config.AppProps;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;

/** Forwards AI-owned endpoints to the Python service, adding the authenticated caller context. */
@Service
public class AiClient {
    private final AppProps props;
    private final HttpClient http = HttpClient.newBuilder()
            .version(HttpClient.Version.HTTP_1_1)
            .connectTimeout(Duration.ofSeconds(3))
            .build();

    public AiClient(AppProps props) {
        this.props = props;
    }

    public Object get(String path, String query) {
        return call("GET", path + (query == null || query.isBlank() ? "" : "?" + query), null, null);
    }

    public Object post(String path, Object body) {
        return call("POST", path, body, "application/json");
    }

    public Object delete(String path) {
        return call("DELETE", path, null, null);
    }

    public Object upload(String path, byte[] content, String filename, String contentType) {
        String boundary = "----medtwin" + UUID.randomUUID().toString().replace("-", "");
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            String header = "--" + boundary + "\r\n"
                    + "Content-Disposition: form-data; name=\"file\"; filename=\""
                    + filename.replace("\"", "") + "\"\r\n"
                    + "Content-Type: " + (contentType == null ? "application/octet-stream" : contentType)
                    + "\r\n\r\n";
            out.write(header.getBytes(StandardCharsets.UTF_8));
            out.write(content);
            out.write(("\r\n--" + boundary + "--\r\n").getBytes(StandardCharsets.UTF_8));
            return call("POST", path, out.toByteArray(), "multipart/form-data; boundary=" + boundary);
        } catch (Exception exc) {
            throw ApiError.unavailable("AI service unavailable.");
        }
    }

    public Map<String, Object> model() {
        try {
            Object result = get("/internal/model/", null);
            if (result instanceof Map<?, ?> raw) {
                @SuppressWarnings("unchecked")
                Map<String, Object> typed = (Map<String, Object>) raw;
                return typed;
            }
        } catch (Exception ignored) {
            // health endpoints must still respond when the AI service is offline
        }
        return J.map("name", "medtwin-offline-composer", "version", "1.0", "mode", "offline");
    }

    private Object call(String method, String path, Object body, String contentType) {
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder()
                    .uri(URI.create(props.getAiServiceUrl().replaceAll("/+$", "") + path))
                    .timeout(Duration.ofSeconds(30))
                    .header("Accept", "application/json");

            Principal user = (Principal) Ctx.req().getAttribute(Ctx.PRINCIPAL);
            if (user != null) {
                builder.header("X-Medtwin-User-Id", user.id)
                        .header("X-Medtwin-User-Role", user.role)
                        .header("X-Medtwin-User-Email", user.email)
                        .header("X-Medtwin-User-Language", user.language.isEmpty() ? "en" : user.language);
            }
            if (!props.getAiSharedSecret().isBlank()) {
                builder.header("X-Medtwin-AI-Secret", props.getAiSharedSecret());
            }

            HttpRequest.BodyPublisher publisher;
            if (body instanceof byte[] bytes) {
                publisher = HttpRequest.BodyPublishers.ofByteArray(bytes);
                builder.header("Content-Type", contentType);
            } else if (body != null) {
                publisher = HttpRequest.BodyPublishers.ofString(J.toJson(body));
                builder.header("Content-Type", "application/json");
            } else {
                publisher = HttpRequest.BodyPublishers.noBody();
            }
            HttpRequest request = builder.method(method, publisher).build();
            HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() >= 400) {
                String message = "AI service request failed.";
                try {
                    Map<?, ?> parsed = J.JSON.readValue(response.body(), Map.class);
                    Object detail = parsed.get("error");
                    if (detail != null) message = J.s(detail);
                } catch (Exception ignored) {
                    // keep the generic message
                }
                throw new ApiError(response.statusCode(), message);
            }
            if (response.body() == null || response.body().isBlank()) return J.map();
            return J.JSON.readValue(response.body(), Object.class);
        } catch (ApiError exc) {
            throw exc;
        } catch (Exception exc) {
            throw ApiError.unavailable("AI service unavailable.");
        }
    }
}
