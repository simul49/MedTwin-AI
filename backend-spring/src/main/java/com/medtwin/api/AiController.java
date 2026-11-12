package com.medtwin.api;

import com.medtwin.core.*;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

/**
 * The AI/LLM boundary. Spring owns authentication, roles and the HTTP contract;
 * the Python service owns intent, retrieval, generation, safety and NLP.
 */
@RestController
public class AiController {
    private final AiClient ai;
    private final Access access;

    public AiController(AiClient ai, Access access) {
        this.ai = ai;
        this.access = access;
    }

    @PostMapping("/ai/chat/")
    public Object chat(@RequestBody(required = false) java.util.Map<String, Object> body) {
        return ai.post("/ai/chat/", body);
    }

    /** Anonymous website chatbot — general health Q&A with the same safety pipeline. */
    @PostMapping("/ai/public-chat/")
    public Object publicChat(@RequestBody(required = false) java.util.Map<String, Object> body) {
        return ai.post("/public-chat/", body);
    }

    @GetMapping("/ai/conversations/")
    public Object conversations(HttpServletRequest request) {
        access.require("PATIENT");
        return ai.get("/ai/conversations/", request.getQueryString());
    }

    @GetMapping("/ai/conversations/{id}/")
    public Object conversation(@PathVariable String id) {
        return ai.get("/ai/conversations/" + id + "/", null);
    }

    @DeleteMapping("/ai/conversations/{id}/")
    public ResponseEntity<Void> deleteConversation(@PathVariable String id) {
        ai.delete("/ai/conversations/" + id + "/");
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/ai/history/")
    public Object history() {
        return ai.get("/ai/history/", null);
    }

    @GetMapping("/recommendations/")
    public Object recommendations() {
        access.require("PATIENT");
        return ai.get("/recommendations/", null);
    }

    @PostMapping("/recommendations/{id}/feedback/")
    public Object recommendationFeedback(@PathVariable String id,
                                         @RequestBody(required = false) java.util.Map<String, Object> body) {
        access.require("PATIENT");
        return ai.post("/recommendations/" + id + "/feedback/", body);
    }

    @PostMapping("/safety/evaluate/")
    public Object evaluateSafety(@RequestBody(required = false) java.util.Map<String, Object> body) {
        access.require("DOCTOR", "ADMIN");
        return ai.post("/safety/evaluate/", body);
    }

    @GetMapping("/content-analysis/")
    public Object contentAnalysis() {
        return ai.get("/content-analysis/", null);
    }

    @PostMapping("/content-analysis/")
    public ResponseEntity<Object> analyseContent(@RequestParam("file") MultipartFile file)
            throws IOException {
        Object result = ai.upload("/content-analysis/", file.getBytes(),
                file.getOriginalFilename() == null ? "upload.png" : file.getOriginalFilename(),
                file.getContentType());
        return ResponseEntity.status(201).body(result);
    }
}
