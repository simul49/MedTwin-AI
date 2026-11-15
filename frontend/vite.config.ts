import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  // The Vite entry (index.html) lives at the repo root, outside frontend/.
  root: fileURLToPath(new URL('..', import.meta.url)),
  build: {
    // Keep build output in frontend/dist (used by nginx in Docker).
    outDir: fileURLToPath(new URL('./dist', import.meta.url)),
    emptyOutDir: true,
  },
  plugins: [vue()],
  css: {
    // Vite searches for postcss.config.js from the project root, which is the
    // repo root now — point it back at the frontend folder explicitly.
    postcss: fileURLToPath(new URL('./postcss.config.js', import.meta.url)),
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    fs: {
      // Allow serving files from the repo root (index.html + frontend/src).
      allow: [fileURLToPath(new URL('..', import.meta.url))],
    },
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
