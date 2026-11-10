import logging

from django.conf import settings
from django.db.utils import DatabaseError, OperationalError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

logger = logging.getLogger(__name__)


class CorsMiddleware:
    """Minimal CORS support so the Vue SPA can call the API from another port.

    Only origins listed in ``CORS_ALLOWED_ORIGINS`` are accepted; credentials
    (the session cookie) are allowed for those origins only (PRD §23.1).
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed = {o.strip().rstrip("/") for o in getattr(settings, "CORS_ALLOWED_ORIGINS", []) if o.strip()}
        self.headers = ", ".join(
            getattr(settings, "CORS_ALLOW_HEADERS", ["content-type", "x-csrftoken", "x-requested-with"])
        )

    def _permit(self, origin: str) -> bool:
        return bool(origin) and (origin.rstrip("/") in self.allowed or "*" in self.allowed)

    def _decorate(self, response, origin: str):
        response["Access-Control-Allow-Origin"] = "*" if "*" in self.allowed else origin
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = self.headers
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Max-Age"] = "86400"
        response["Vary"] = "Origin"
        return response

    def __call__(self, request):
        origin = request.META.get("HTTP_ORIGIN", "")

        if request.method == "OPTIONS" and self._permit(origin):
            response = HttpResponse(status=200)
            response["Content-Length"] = "0"
            return self._decorate(response, origin)

        response = self.get_response(request)
        if self._permit(origin):
            response = self._decorate(response, origin)
        return response


class DatabaseUnavailableMiddleware:
    """Turn "MySQL is down" into a clear, actionable response.

    Uses ``process_exception`` because Django converts view exceptions into a
    500 response before any outer ``__call__`` wrapper would see them.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, (OperationalError, DatabaseError)):
            return None

        logger.warning("database unavailable: %s", exception)
        db_name = settings.DATABASES.get("default", {}).get("NAME", "")

        if request.path.startswith("/api/"):
            return JsonResponse(
                {
                    "error": "Database unavailable.",
                    "database": db_name,
                    "detail": str(exception)[:300],
                },
                status=503,
            )

        return render(
            request,
            "setup.html",
            {
                "database": db_name,
                "detail": str(exception)[:300],
            },
            status=503,
        )
