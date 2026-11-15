package com.medtwin.config;

import com.medtwin.core.Principal;
import com.medtwin.core.Realtime;
import com.medtwin.core.Sessions;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.util.Map;

/**
 * Registers the authenticated real-time socket at "/ws/realtime".
 *
 * The MVC AuthInterceptor already authenticates the HTTP handshake (GET with
 * session cookie); this interceptor additionally stores the resolved Principal
 * on the socket session so Realtime knows which user it serves.
 */
@Configuration
@EnableWebSocket
public class RealtimeConfig implements WebSocketConfigurer {

    private final Realtime realtime;
    private final Sessions sessions;
    private final AppProps props;

    public RealtimeConfig(Realtime realtime, Sessions sessions, AppProps props) {
        this.realtime = realtime;
        this.sessions = sessions;
        this.props = props;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(realtime, "/ws/realtime")
                .addInterceptors(new PrincipalInterceptor())
                .setAllowedOriginPatterns(props.getCorsOrigins().split(","));
    }

    private class PrincipalInterceptor implements HandshakeInterceptor {
        @Override
        public boolean beforeHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                       WebSocketHandler wsHandler, Map<String, Object> attributes) {
            if (request instanceof ServletServerHttpRequest servlet) {
                Principal user = sessions.resolve(servlet.getServletRequest());
                if (user == null) return false; // reject unauthenticated sockets
                attributes.put("principal", user);
                return true;
            }
            return false;
        }

        @Override
        public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                                   WebSocketHandler wsHandler, Exception exception) {
            // nothing to do
        }
    }
}
