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
    // The dev entry is dev.html at the repo root; CI renames the built output
    // to index.html and publishes it at the repo root for GitHub Pages.
    rollupOptions: {
      input: 'dev.html',
    },
  },
  plugins: [
    vue(),
    {
      // The root index.html is the landing page; the app dev entry is dev.html.
      // Serve the app at "/" and fall back to it for SPA routes (/login, ...)
      // so vue-router history mode works in dev. /index.html stays the landing.
      name: 'serve-dev-entry',
      apply: 'serve',
      configureServer(server) {
        server.middlewares.use((req, _res, next) => {
          const url = (req.url || '').split('?')[0];
          const isViteInternal =
            url.startsWith('/@') ||
            url.startsWith('/.vite') ||
            url.startsWith('/node_modules');
          const isOtherAsset =
            url.includes('.') ||
            url.startsWith('/api') ||
            url.startsWith('/ws') ||
            url.startsWith('/site');
          if (url === '/' || url === '/dev.html') {
            req.url = '/dev.html';
          } else if (!isViteInternal && !isOtherAsset && url !== '/index.html') {
            req.url = '/dev.html';
          }
          next();
        });
      },
    },
  ],
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
