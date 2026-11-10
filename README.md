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
| Backend | Python 3.9 + Django 4.2 + Django REST Framework |
| Database | MySQL 8.4 — database `medtwin`, user `root`, no password |
| AI | Built-in offline engine (extractive RAG + rules). Optional LLM provider via env vars |

The AI layer has **no hard dependency on an external model provider**. The app is fully functional
out of the box; when you share an API key later, set two environment variables and the same
endpoints start using it (see [Enabling an LLM provider](#enabling-an-llm-provider)).

---

## Quick start

```bash
# 1. Database (once)
mysql -u root -e "CREATE DATABASE IF NOT EXISTS medtwin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root medtwin < db/schema.sql

# 2. Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py seed_demo          # synthetic demo data
.venv/bin/python manage.py runserver 127.0.0.1:8001

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev                                   # http://localhost:5173
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
│   └── schema.sql                # Source of truth for the schema (27 tables)
├── backend/                      # Django + DRF
│   ├── config/                   # settings, urls, wsgi/asgi
│   ├── apps/
│   │   ├── accounts/             # users, roles, profiles, session auth
│   │   ├── twin/                 # records, observations, allergies, meds, documents, timeline
│   │   ├── consent/              # consent grants and the access workflow
│   │   ├── ai/                   # assistant, RAG, safety engine, recommendations
│   │   ├── connect/              # messages, appointments, notifications
│   │   └── ops/                  # audit logs, model governance, admin, feature flags
│   └── templates/setup.html      # guided setup page when MySQL is unreachable
└── frontend/                     # Vue 3 SPA
    └── src/
        ├── api/                  # typed client + endpoint modules
        ├── components/           # layout + UI kit
        ├── i18n/                 # en / zh message catalogues
        ├── stores/               # auth + ui (Pinia)
        └── views/                # public, patient, doctor, admin, errors
```

### Why `managed = False`

Every Django model mirrors `db/schema.sql` exactly and is declared `managed = False`, so the SQL file
— not Django migrations — is the schema's source of truth. This keeps MySQL-specific definitions
(`ENUM`, `JSON`, `FULLTEXT`, precise indexes) authoritative and readable in one place.

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
* Session cookie (`httpOnly`, SameSite=Lax) + CSRF token; the SPA echoes `X-CSRFToken` on unsafe
  methods and refreshes it after login (Django rotates it).
* Passwords hashed with PBKDF2-SHA256; sign-in is rate-limited (8 attempts / 15 min per email+IP).
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
