# MedTwin AI

**Real-World Medical & Healthcare Digital Twin & AI Safety Platform**

MedTwin AI turns authorised health information into a structured **Digital Twin** and explains it
with a grounded, safety-aware **AI assistant** — with healthcare professionals kept in the loop.

> MedTwin AI provides information and organisational support. It is **not** a diagnosis, **not** a
> substitute for professional medical advice, and **not** for emergencies.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Vue 3 + TypeScript + Vite + Tailwind CSS + Pinia + vue-i18n (EN / 中文) |
| Main backend | Java 21 + Spring Boot 3.3 (REST, sessions, RBAC, consent, JDBC) on `:8001` |
| AI backend | Python 3.9 + FastAPI on `:8002` — LLM/RAG/safety/NLP **only** |
| Database | MySQL 8.4 — database `medtwin`, user `root`, no password |
| AI engine | Built-in offline engine (extractive RAG + rules). Optional LLM provider via env vars |

The AI layer has **no hard dependency on an external model provider**. The app is fully functional
out of the box; when you share an API key later, set two environment variables and the same
endpoints start using it (see [Enabling an LLM provider](#enabling-an-llm-provider)).

### Why a hybrid backend

Spring Boot is the only public backend. It owns `/api/v1/*`, session cookies, CSRF, role checks,
consent scoping, audit logging and every SQL read/write. The Python service is an internal
microservice bound to `127.0.0.1:8002`; Spring proxies only the AI-owned routes to it and passes
the authenticated user in `X-Medtwin-*` headers:

```
Vue SPA  ──►  Spring Boot :8001  ──►  MySQL
                    │
                    └── /ai/chat, /ai/history, /ai/conversations, /recommendations,
                        /safety/evaluate, /content-analysis, /internal/extract
                            ──►  Python FastAPI :8002  ──►  MySQL  + optional LLM provider
```

The Python service reuses the existing `apps/ai`, `apps/core` and model modules from `backend/`
as a plain Django ORM — there is **no Django HTTP server** in the running stack. Document text
extraction (PDF text layer and candidate fields) is also Python-owned NLP; Spring writes the file
and stores the relational rows. `MEDTWIN_AI_SHARED_SECRET` can be set on both processes to
authenticate the internal hop.

---

## Quick start

```bash
# 1. Database (once)
mysql -u root -e "CREATE DATABASE IF NOT EXISTS medtwin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root medtwin < db/schema.sql

# 2. Python environment (AI service + demo seeder)
cd backend
python3 -m venv .venv
.venv/bin/pip install -r ../backend-ai/requirements.txt
.venv/bin/python manage.py seed_demo          # synthetic demo data
cd ..

# 3. Both backend processes (Java 21 + Gradle required)
chmod +x scripts/start-backend.sh
./scripts/start-backend.sh
#   Spring Boot :8001/api/v1   ·   Python AI :8002

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev                                   # http://localhost:5173
```

To run the two services separately:

```bash
backend/.venv/bin/python -m uvicorn app:app --app-dir backend-ai --host 127.0.0.1 --port 8002
cd backend-spring && JAVA_HOME=/opt/homebrew/opt/openjdk@21 gradle bootRun
```

Open **http://localhost:5173** and sign in with a demo account (password `MedTwin@2026` for all):

| Role | Email |
|---|---|
| Patient | `patient@medtwin.dev` |
| Patient (second) | `marc@medtwin.dev` |
| Doctor | `doctor@medtwin.dev` |
| Doctor (second) | `amara@medtwin.dev` |
| Administrator | `admin@medtwin.dev` |

All seeded data is **synthetic**. There is no real patient information anywhere in this repository.

---

## Repository layout

```
.
├── db/
│   └── schema.sql                # Source of truth for the schema (29 tables)
├── backend-spring/               # Spring Boot 3 — public API, auth, RBAC, consent, JDBC
│   └── src/main/java/com/medtwin/
│       ├── api/                  # controllers: auth, patient, doctor, consent, connect, ops, AI proxy
│       ├── core/                 # sessions, PBKDF2, CSRF, access control, serializers, AI client
│       └── config/               # properties, interceptors/CORS, error handling
├── backend-ai/                   # FastAPI — LLM, RAG, safety, recommendations, document NLP
│   ├── app.py
│   └── requirements.txt
├── backend/                      # Python modules + Django ORM models (no HTTP server)
│   ├── apps/ai/                  # intent, retrieval, composer, providers, safety, content
│   ├── apps/core/                # audit + shared helpers
│   ├── apps/*/models.py          # unmanaged models shared by the AI service
│   └── manage.py seed_demo       # synthetic demo data
├── scripts/start-backend.sh      # starts both backend processes
└── frontend/                     # Vue 3 SPA (unchanged)
    └── src/api/                  # typed client + endpoint modules
```

### Why `managed = False`

Every Django model mirrors `db/schema.sql` exactly and is declared `managed = False`, so the SQL file
— not migrations — is the schema's source of truth. Spring issues explicit SQL over the same tables
and the Python AI service reuses the model definitions for its ORM queries. This keeps
MySQL-specific definitions (`ENUM`, `JSON`, `FULLTEXT`, precise indexes) authoritative in one place.

---

## What is implemented

### Public website
Home, About Us, Solutions, How It Works, Research, Trust & Safety, Privacy, Terms, Medical
Disclaimer, Contact — with the specified navbar (brand on the left, the five primary links grouped in
the centre, language selector and Patient/Doctor portal selector on the right) and a footer carrying
the full project name and the medical disclaimer in both languages.

### Patient
Digital Twin, health records, observations, allergies, medications, timeline, document upload with
reviewable extraction, AI assistant, educational recommendations, consent & sharing, appointments,
messaging, notifications, settings (profile, language, password, export, delete).

### Healthcare professional
Authorised-patient workspace limited to granted scope, patient summary with an AI **draft** summary
(always marked unverified), records / results / medications / allergies / documents / timeline,
appointment handling, secure messaging, and a standalone safety evaluator for draft answers.

### Administrator
Users and roles, professional verification, access oversight, approved knowledge sources, audit log
review, feature & release status, and system health.

---

## AI design

One assistant turn runs through explicit, testable stages:

```
intent + risk  →  retrieval (approved knowledge)  →  patient context (authorised, minimal)
              →  generation (offline composer or LLM)  →  safety evaluation  →  persist
```

**Retrieval** is lexical (TF-IDF style) over `knowledge_chunks` whose source is `APPROVED`;
`RESTRICTED` chunks require a clinical caller. Patient documents are never part of the general corpus.

**Generation** — with no provider configured, the offline composer produces an *extractive* answer:
every statement comes from a retrieved passage or the patient's own twin, citations are inline, and
anything unsupported is stated as a limitation. Nothing medical is invented.

**Trust & Safety** scores seven named factors before a response is shown:

| Factor | Weight | What it checks |
|---|---:|---|
| Knowledge grounding | 0.24 | Are claims tied to retrieved passages? |
| Reference availability | 0.12 | Were approved sources available at all? |
| Patient context match | 0.14 | Is authorised context used and labelled? |
| Contradiction check | 0.14 | Conflicts with the Digital Twin (e.g. a recorded allergy) |
| Safety rules | 0.20 | Diagnosis, prescription and dose-change language |
| Unsupported claims | 0.10 | Absolute or guaranteed statements |
| Risk routing | 0.06 | Emergency / out-of-scope escalation |

The indicator is an **evaluation aid, not a guarantee of medical correctness**; a high value never
bypasses safety rules. Emergency language short-circuits generation and returns escalation guidance.

### Enabling an LLM provider

```bash
export MEDTWIN_LLM_PROVIDER=openai_compatible   # or "anthropic"
export MEDTWIN_LLM_API_KEY=sk-...               # your key
export MEDTWIN_LLM_MODEL=gpt-4o-mini
```

The provider is called with a system prompt that forbids diagnosis, prescribing and dose changes and
requires inline citations. If the call fails, the request **falls back to the offline composer**
rather than showing an error, and the limitation is recorded in the response.

---

## Security and privacy

* Backend-enforced authorisation: a doctor only reaches a patient while an effective, in-scope,
  un-expired grant exists. Missing grants return **404**, so endpoints cannot probe for patient IDs.
* Spring-issued session cookie (`httpOnly`, SameSite=Lax, 8 h) + `medtwin_csrf` token; the SPA
  echoes `X-CSRFToken` on unsafe methods and refreshes it after login. Sessions live in the
  existing `django_session` table with a plain JSON payload.
* Passwords hashed with PBKDF2-SHA256; Spring verifies and writes the same Django hash format, so
  existing seeded accounts keep working. Sign-in is rate-limited (8 attempts / 15 min per email+IP).
* The Python AI service binds to `127.0.0.1` only and never accepts browser traffic directly.
* Uploaded files are validated by extension, MIME type and size, stored outside the public tree, and
  served only through an authorised view.
* Sensitive access, consent changes and privileged actions are written to `audit_logs` with actor,
  outcome, IP and trace ID.
* Uploads are limited to PDF/PNG/JPEG at 15 MB. No OCR is configured, so scanned images yield no
  extracted text — the UI says so instead of inventing values.

---

## Known limitations

* **No OCR.** PDFs need a text layer; scanned images are stored but not read.
* **Messaging polls every 10 s.** WebSockets are planned, not implemented.
* **Synthetic-content analysis is experimental** — indicator heuristics with stated uncertainty, not a
  validated detector.
* **Password reset** returns the token in the API response because no mail server is configured.
* **Resource limits** (max file size, request size, model timeout) are documented but not enforced
  per user or role.
* The public website lists no validated performance metrics or publications.

---

## API

All endpoints live under `/api/v1/`. A few entry points:

```
POST /api/v1/auth/csrf/          GET  /api/v1/health/
POST /api/v1/auth/login/         POST /api/v1/auth/logout/
GET  /api/v1/patient/digital-twin/     POST /api/v1/ai/chat/
GET  /api/v1/doctor/authorized-patients/
GET  /api/v1/admin/system/health/
```

`backend/README.md` and `frontend/README.md` contain the full route map and frontend conventions.
