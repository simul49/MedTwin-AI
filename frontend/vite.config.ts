import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import { resolve } from 'node:path';

// npm scripts and CI run Vite from frontend/, while the HTML entry is at the
// repository root. Resolve the entry to an absolute path so Rollup does not
// interpret it relative to the frontend working directory.
const repoRoot = fileURLToPath(new URL('..', import.meta.url));

export default defineConfig({
  root: repoRoot,
  build: {
    // Keep build output in frontend/dist (used by nginx in Docker).
    outDir: fileURLToPath(new URL('./dist', import.meta.url)),
    emptyOutDir: true,
    // The dev entry is at the repository root; CI renames its built output
    // to index.html before publishing it to GitHub Pages.
    rollupOptions: {
      input: resolve(repoRoot, 'dev.html'),
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
      allow: [repoRoot],
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
