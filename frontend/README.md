# MedTwin AI — frontend (Vue 3 + TypeScript + Vite)

```bash
npm install
npm run dev        # http://localhost:5173 (proxies /api to Django on :8001)
npm run build      # vue-tsc --noEmit && vite build
npm run typecheck
```

## Structure

```
src/
├── api/
│   ├── client.ts       # fetch wrapper: CSRF handling + one retry after login rotation
│   ├── endpoints.ts    # typed calls grouped by domain (auth, patient, consent, ai, …)
│   └── types.ts        # shared response types
├── components/
│   ├── layout/         # PublicNav (spec navbar), PublicFooter
│   └── ui/             # AppCard, StatCard, StatusBadge, EmptyState, SafetyPanel, MedicalDisclaimer
├── composables/useAsync.ts   # loading/error/data helper + date and byte formatters
├── i18n/               # en.ts / zh.ts catalogues (add new keys to BOTH)
├── router.ts           # role-guarded routes
├── stores/             # auth (session, role), ui (locale, toasts)
└── views/              # public/, patient/, doctor/, admin/, errors/, layouts/
```

## Conventions

* **Styling** — Tailwind utilities plus the component classes in `src/style.css`
  (`.card`, `.btn-primary`, `.input`, `.chip`, `.muted`, `.prose-answer`, …). Palette: `brand-*`
  (blue) and `ink-*` (slate).
* **i18n** — `const { t } = useI18n()`. Add any new key to **both** `en.ts` and `zh.ts`.
* **Data loading** — `useAsync(() => api.call())` returns `{ data, loading, error, run }`.
* **API calls** — always via `src/api/endpoints.ts`; never build URLs inline.
* **Accessibility** — labels are bound to inputs, links carry visible focus rings, and status is
  conveyed with text (not colour alone).

## Auth flow

1. `GET /api/v1/auth/csrf/` on first unsafe request (token cached from the `medtwin_csrf` cookie).
2. `POST /api/v1/auth/login/` → Django rotates CSRF → the client refreshes it automatically.
3. A `403` from a stale token triggers one refresh-and-retry inside `client.ts`.

The Vite proxy keeps `/api` first-party, so the session cookie stays same-site and no CORS
credentials dance is needed in development.
