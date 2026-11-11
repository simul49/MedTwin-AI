"""Settings for the MedTwin AI backend.

Secrets are never hard-coded: every value that could differ per environment is
read from the process environment with a safe local default (PRD §20.2).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    """Load ``KEY=VALUE`` lines into the environment (existing values win).

    Keeps secrets such as ``MEDTWIN_LLM_API_KEY`` out of the repository — the
    ``backend/.env`` file is git-ignored.
    """
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        os.environ.setdefault(key, value)


_load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    return env(key, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = env("DJANGO_SECRET_KEY", "django-insecure-dev-only-medtwin-ai-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)

# The Vue dev server runs on :5173; add your production origin when deploying.
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "*").split(",") if h]

INSTALLED_APPS = [
    # apps.core ships the `runserver` override and shared middleware.
    "apps.core",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts",
    "apps.twin",
    "apps.consent",
    "apps.ai",
    "apps.connect",
    "apps.ops",
]

MIDDLEWARE = [
    "apps.core.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.DatabaseUnavailableMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

# ---------------------------------------------------------------------------
# Database — MySQL is the source of truth (PRD §21). The schema is owned by
# db/schema.sql, so every model declares managed = False.
# ---------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", "medtwin"),
        "USER": env("DB_USER", "root"),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "127.0.0.1"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4", "init_command": "SET sql_mode='STRICT_TRANS_TABLES'"},
        "CONN_MAX_AGE": 60,
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "medtwin_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 60 * 60 * 8
CSRF_COOKIE_NAME = "medtwin_csrf"
CSRF_COOKIE_HTTPONLY = False  # the SPA must read it to echo the header
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_TRUSTED_ORIGINS = [
    o for o in env("DJANGO_CSRF_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o
]

# ---------------------------------------------------------------------------
# SPA (Vue 3) integration
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o for o in env("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o
]
CORS_ALLOW_HEADERS = ["content-type", "x-csrftoken", "x-requested-with"]

# ---------------------------------------------------------------------------
# AI provider abstraction (PRD §20.1, §24)
# No provider is configured by default: the assistant runs on the built-in
# offline engine. Set MEDTWIN_LLM_PROVIDER + MEDTWIN_LLM_API_KEY to enable one.
# ---------------------------------------------------------------------------
MEDTWIN_LLM_PROVIDER = env("MEDTWIN_LLM_PROVIDER", "")  # "openai_compatible" | "anthropic"
MEDTWIN_LLM_API_KEY = env("MEDTWIN_LLM_API_KEY", "")
MEDTWIN_LLM_MODEL = env("MEDTWIN_LLM_MODEL", "gpt-4o-mini")
MEDTWIN_LLM_BASE_URL = env("MEDTWIN_LLM_BASE_URL", "https://api.openai.com/v1")
MEDTWIN_EMBEDDING_PROVIDER = env("MEDTWIN_EMBEDDING_PROVIDER", "")
MEDTWIN_EMBEDDING_MODEL = env("MEDTWIN_EMBEDDING_MODEL", "text-embedding-3-small")
MEDTWIN_AI_TIMEOUT_MS = int(env("MEDTWIN_AI_TIMEOUT_MS", "15000"))

# ---------------------------------------------------------------------------
# Uploads — stored outside the public static tree, served by an authorized view
# (PRD §10.3).
# ---------------------------------------------------------------------------
MEDIA_ROOT = BASE_DIR / "var" / "documents"
MEDIA_URL = "/media/"
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_UPLOAD_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "var" / "static"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# Passwords: Django's PBKDF2-SHA256 hasher with its default iterations.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {"django.utils.autoreload": {"level": "WARNING"}},
}
