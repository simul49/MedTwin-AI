"""Small shared helpers: identifiers, audit logging, request metadata."""
import json
import logging
import uuid
from typing import Any, Optional

from django.http import HttpRequest

logger = logging.getLogger(__name__)


def new_id() -> str:
    """Generate an application-side primary key (VARCHAR(36))."""
    return str(uuid.uuid4())


def trace_id() -> str:
    return uuid.uuid4().hex[:32]


def json_default(value: Any) -> Any:
    """Coerce values (dates, decimals) into JSON-safe primitives."""
    return json.loads(json.dumps(value, default=str))


def client_ip(request: Optional[HttpRequest]) -> str:
    if request is None:
        return ""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""


def user_agent(request: Optional[HttpRequest]) -> str:
    if request is None:
        return ""
    return (request.META.get("HTTP_USER_AGENT", "") or "")[:255]


def record_audit(
    *,
    action: str,
    request: Optional[HttpRequest] = None,
    actor=None,
    resource_type: str = "",
    resource_id: str = "",
    outcome: str = "SUCCESS",
    metadata: Any = None,
) -> None:
    """Write an audit event. Never raises — auditing must not break a request."""
    from apps.ops.models import AuditLog  # local import avoids app-load cycles

    user = actor if actor is not None else getattr(request, "user", None)
    actor_id = getattr(user, "id", None) if user and getattr(user, "is_authenticated", False) else None
    actor_email = getattr(user, "email", None) if actor_id else None

    try:
        AuditLog.objects.create(
            id=new_id(),
            actor_id=actor_id,
            actor_email=actor_email or (getattr(user, "email", "") if user else ""),
            action=action,
            resource_type=resource_type or "",
            resource_id=resource_id or "",
            outcome=outcome,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
            trace_id=trace_id(),
            metadata=json_default(metadata) if metadata is not None else None,
        )
    except Exception as exc:  # pragma: no cover - audit must never break a flow
        logger.warning("audit write failed for %s: %s", action, exc)
