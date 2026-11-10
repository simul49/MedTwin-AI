"""Authorization helpers.

Backend enforcement is the only enforcement that counts (PRD §8.2): every
protected endpoint verifies role, ownership and — for doctors — an active
consent grant before returning a single field.
"""
from functools import wraps
from typing import Optional

from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.accounts.models import ROLE_ADMIN, ROLE_DOCTOR, ROLE_PATIENT, User
from apps.consent.models import ConsentGrant
from apps.core.utils import record_audit


def require_roles(*roles):
    """View-method decorator enforcing role membership."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            user = request.user
            if not getattr(user, "is_authenticated", False):
                raise PermissionDenied("Authentication required.")
            if user.role not in roles:
                record_audit(
                    action="ACCESS_DENIED",
                    request=request,
                    actor=user,
                    resource_type="role",
                    outcome="DENIED",
                    metadata={"required": list(roles)},
                )
                raise PermissionDenied("Your role does not allow this action.")
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def active_grant(doctor, patient) -> Optional[ConsentGrant]:
    """Return the grant that currently authorises `doctor` for `patient`."""
    return (
        ConsentGrant.objects.filter(doctor=doctor, patient=patient, status="ACTIVE")
        .order_by("-created_at")
        .first()
    )


def grant_is_live(grant: Optional[ConsentGrant]) -> bool:
    return bool(grant and grant.is_effective())


def resolve_patient_for(user, patient_id: str) -> User:
    """Resolve a patient the caller is allowed to read.

    Doctors without an effective grant get 404 (not 403) so the endpoint cannot
    be used to probe which patient IDs exist.
    """
    try:
        patient = User.objects.get(pk=patient_id, role=ROLE_PATIENT)
    except User.DoesNotExist:
        raise NotFound("Patient not found.")

    if user.role == ROLE_ADMIN:
        return patient
    if user.role == ROLE_PATIENT:
        if patient.id != user.id:
            raise NotFound("Patient not found.")
        return patient
    if user.role == ROLE_DOCTOR:
        if grant_is_live(active_grant(user, patient)):
            return patient
        record_audit(
            action="ACCESS_DENIED",
            actor=user,
            resource_type="patient",
            resource_id=patient_id,
            outcome="DENIED",
            metadata={"reason": "no_active_grant"},
        )
        raise NotFound("Patient not found.")
    raise PermissionDenied("Your role does not allow this action.")


def grant_scope(user, patient) -> list:
    """Scope keys a doctor may read for a patient (patients read everything)."""
    if user.role == ROLE_PATIENT and patient.id == user.id:
        return ["all"]
    if user.role == ROLE_ADMIN:
        return ["all"]
    grant = active_grant(user, patient)
    return (grant.scope if grant else []) or []


def patient_queryset_for_doctor(doctor):
    """Patients a doctor currently holds an effective grant for."""
    grants = ConsentGrant.objects.filter(doctor=doctor, status="ACTIVE").select_related("patient")
    now = timezone.now()
    ids = [g.patient_id for g in grants if not g.expires_at or g.expires_at > now]
    return User.objects.filter(id__in=ids, role=ROLE_PATIENT)


__all__ = [
    "require_roles",
    "active_grant",
    "grant_is_live",
    "resolve_patient_for",
    "grant_scope",
    "patient_queryset_for_doctor",
    "ROLE_PATIENT",
    "ROLE_DOCTOR",
    "ROLE_ADMIN",
]
