package com.medtwin.core;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Real-time hub over a single authenticated WebSocket endpoint.
 *
 * Responsibilities:
 *  - push server events to users (new messages, notifications, payment receipts)
 *  - room presence + offer/answer/ICE relay for WebRTC video consultations
 *
 * Authentication happens on the HTTP handshake (AuthInterceptor resolves the
 * session cookie), so every socket here is already tied to a Principal.
 */
@Component
public class Realtime extends TextWebSocketHandler {

    /** userId -> open sockets (multiple tabs are fine). */
    private final Map<String, Set<WebSocketSession>> byUser = new ConcurrentHashMap<>();
    /** room code -> member userIds. */
    private final Map<String, Set<String>> rooms = new ConcurrentHashMap<>();

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        Principal user = principalOf(session);
        if (user == null) return;
        JsonNode node;
        try {
            node = J.JSON.readTree(message.getPayload());
        } catch (Exception ignored) {
            return;
        }
        String type = node.path("type").asText(null);
        if (type == null) return;

        switch (type) {
            case "join" -> {
                String room = textOrNull(node.get("room"));
                if (room == null || room.isBlank()) return;
                rooms.computeIfAbsent(room, k -> ConcurrentHashMap.newKeySet()).add(user.id);
                pushToRoom(room, J.map(
                        "type", "room-users",
                        "room", room,
                        "users", roomMembers(room)), null);
            }
            case "leave" -> {
                String room = textOrNull(node.get("room"));
                if (room == null) return;
                Set<String> members = rooms.get(room);
                if (members != null && members.remove(user.id)) {
                    pushToRoom(room, J.map(
                            "type", "peer-left",
                            "room", room,
                            "userId", user.id), user.id);
                }
            }
            case "signal" -> {
                String room = textOrNull(node.get("room"));
                String to = textOrNull(node.get("to"));
                if (room == null || to == null) return;
                Set<String> members = rooms.get(room);
                if (members == null || !members.contains(user.id) || !members.contains(to)) return;
                pushToUser(to, J.map(
                        "type", "signal",
                        "room", room,
                        "from", user.id,
                        "data", node.get("data")));
            }
            default -> { /* unknown client types are ignored */ }
        }
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        Principal user = principalOf(session);
        if (user == null) return;
        byUser.computeIfAbsent(user.id, k -> ConcurrentHashMap.newKeySet()).add(session);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        Principal user = principalOf(session);
        if (user == null) return;
        Set<WebSocketSession> sockets = byUser.get(user.id);
        if (sockets != null) {
            sockets.remove(session);
            if (sockets.isEmpty()) byUser.remove(user.id);
        }
        for (Map.Entry<String, Set<String>> room : rooms.entrySet()) {
            if (room.getValue().remove(user.id)) {
                pushToRoom(room.getKey(), J.map(
                        "type", "peer-left",
                        "room", room.getKey(),
                        "userId", user.id), user.id);
            }
        }
    }

    /** Push a JSON payload to every open socket of one user. */
    public void pushToUser(String userId, Map<String, Object> payload) {
        if (userId == null || userId.isBlank()) return;
        Set<WebSocketSession> sockets = byUser.get(userId);
        if (sockets == null) return;
        String text = J.toJson(payload);
        for (WebSocketSession session : new ArrayList<>(sockets)) send(session, text);
    }

    /** Push to every member of a room except {@code excludeUserId} (nullable). */
    public void pushToRoom(String room, Map<String, Object> payload, String excludeUserId) {
        for (String userId : roomMembers(room)) {
            if (excludeUserId != null && excludeUserId.equals(userId)) continue;
            pushToUser(userId, payload);
        }
    }

    public boolean isOnline(String userId) {
        Set<WebSocketSession> sockets = byUser.get(userId);
        return sockets != null && !sockets.isEmpty();
    }

    public List<String> roomMembers(String room) {
        Set<String> members = rooms.get(room);
        return members == null ? List.of() : new ArrayList<>(members);
    }

    private void send(WebSocketSession session, String text) {
        try {
            if (session.isOpen()) session.sendMessage(new TextMessage(text));
        } catch (Exception ignored) {
            // socket died mid-send — the close handler cleans it up
        }
    }

    private Principal principalOf(WebSocketSession session) {
        Object value = session.getAttributes().get("principal");
        return value instanceof Principal principal ? principal : null;
    }

    private String textOrNull(JsonNode node) {
        return node == null || node.isNull() ? null : node.asText(null);
    }
}
