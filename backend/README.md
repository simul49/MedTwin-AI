# MedTwin AI — Python modules (AI service + ORM models)

> The public HTTP backend is now **Spring Boot 3** (`backend-spring/`). This directory no longer
> runs a Django HTTP server; it supplies the Python AI engine, the unmanaged Django ORM models
> shared with the AI microservice (`backend-ai/`), and the demo seed command. See the root
> `README.md` for the current startup commands.

## Setup (AI service / demo data)

```bash
python3 -m venv .venv
.venv/bin/pip install -r ../backend-ai/requirements.txt

mysql -u root -e "CREATE DATABASE IF NOT EXISTS medtwin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
mysql -u root medtwin < ../db/schema.sql

.venv/bin/python manage.py seed_demo
cd .. && ./scripts/start-backend.sh
```

## Configuration (environment variables, all optional)

| Variable | Default | Purpose |
|---|---|---|
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | `medtwin` / `root` / *(empty)* / `127.0.0.1` / `3306` | MySQL connection |
| `DJANGO_SECRET_KEY` | dev value | Never commit a real key |
| `DJANGO_DEBUG` | `1` | Set to `0` in production |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | SPA origins allowed with cookies |
| `DJANGO_CSRF_ORIGINS` | same as above | CSRF-trusted origins |
| `MEDTWIN_LLM_PROVIDER` | *(empty)* | `openai_compatible` or `anthropic` |
| `MEDTWIN_LLM_API_KEY` | *(empty)* | Provider key — leave empty for the offline engine |
| `MEDTWIN_LLM_MODEL` / `MEDTWIN_LLM_BASE_URL` | `gpt-4o-mini` / OpenAI | Provider routing |

## Route map (`/api/v1/`)

**Auth** — `auth/csrf/`, `auth/register/`, `auth/login/`, `auth/logout/`,
`auth/password/change/`, `auth/password/forgot/`, `auth/password/reset/`, `me/`, `doctors/`

**Digital Twin** — `patient/digital-twin/`, `patient/records[/<id>]/`, `patient/timeline/`,
`patient/observations/`, `patient/allergies[/<id>]/`, `patient/medications[/<id>]/`,
`patient/documents[/<id>]/`, `patient/documents/<id>/file/`,
`patient/documents/<id>/extractions/<id>/review/`, `patient/export/`, `patient/data/`

**Consent** — `consent/grants/`, `consent/grants/new/`, `consent/requests/`,
`consent/grants/<id>/decision/`, `consent/grants/<id>/revoke/`

**AI** — `ai/chat/`, `ai/conversations[/<id>]/`, `ai/history/`, `recommendations[/<id>/feedback/]`,
`safety/evaluate/`, `content-analysis/`

**Connect** — `conversations[/<id>]/`, `appointments[/<id>]/`, `notifications[/<id>/read/]`,
`notifications/read-all/`

**Doctor** — `doctor/authorized-patients/`, `doctor/patients/<id>/summary/` (GET + POST draft),
`doctor/patients/<id>/records|documents|timeline/`

**Admin** — `admin/users[/<id>]/`, `admin/audit-logs/`, `admin/consent-grants/`,
`admin/knowledge-sources[/<id>]/`, `admin/system/health/`, `admin/feature-flags[/<id>]/`

**Public** — `health/`

## Notes

* Every model is `managed = False` and mirrors `db/schema.sql`; the SQL file owns the schema.
* `apps/core/management/commands/runserver.py` disables Django's boot-time migration check so the
  server starts even when MySQL is stopped. Data-touching requests then render `templates/setup.html`
  (HTTP 503) or return `{"error": "Database unavailable."}` under `/api/` instead of crashing.
* `apps/core/middleware.py` provides CORS (explicit origins only, credentials allowed) and the
  database-unavailable handler.
* Authorisation lives in `apps/core/permissions.py`; it is enforced server-side on every request.
