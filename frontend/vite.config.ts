import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    // Allow cloudflared quick-tunnel hosts (URL changes on each restart).
    allowedHosts: true,
    proxy: {
      // First-party API calls to Spring Boot :8001; cookies stay same-site and CSRF works normally.
      '/api': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      // Real-time WebSocket (messages, notifications, video signalling).
      // The Spring context path is /api/v1, so the socket lives at /api/v1/ws/realtime.
      '/ws': {
        target: 'ws://127.0.0.1:8001/api/v1',
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
