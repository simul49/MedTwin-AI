"""Consent and professional-access workflow (PRD §8.3).

Every grant, decision and revocation is written to the audit log. A doctor
never receives data unless an effective grant exists at the moment of the
request.
"""
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ROLE_ADMIN, ROLE_DOCTOR, ROLE_PATIENT, User
from apps.consent.models import SCOPE_OPTIONS, ConsentGrant
from apps.consent.serializers import serialize_grant
from apps.connect.models import Notification
from apps.core.permissions import require_roles
from apps.core.utils import new_id, record_audit


def _notify(user, *, type: str, title: str, body: str, link: str = "") -> None:
    Notification.objects.create(
        id=new_id(), user=user, type=type, title=title, body=body, link=link
    )


def _parse_scope(raw) -> list:
    if isinstance(raw, str):
        raw = [part.strip() for part in raw.split(",")]
    scope = [key for key in (raw or []) if key in SCOPE_OPTIONS or key == "all"]
    return scope or ["profile", "conditions"]


class ConsentGrantListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == ROLE_PATIENT:
            grants = ConsentGrant.objects.filter(patient=user).select_related("doctor")
        elif user.role == ROLE_DOCTOR:
            grants = ConsentGrant.objects.filter(doctor=user).select_related("patient")
        elif user.role == ROLE_ADMIN:
            grants = ConsentGrant.objects.all().select_related("doctor", "patient").order_by("-created_at")[:200]
        else:
            grants = ConsentGrant.objects.none()
        return Response({"results": [serialize_grant(g) for g in grants], "scopeOptions": SCOPE_OPTIONS})


class ConsentRequestAPI(APIView):
    """Doctor asks a patient for access (step 1-2 of the workflow)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR)
    def post(self, request):
        data = request.data
        patient_id = data.get("patientId") or ""
        try:
            patient = User.objects.get(pk=patient_id, role=ROLE_PATIENT)
        except User.DoesNotExist:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        existing = ConsentGrant.objects.filter(
            doctor=request.user, patient=patient, status__in=["PENDING", "ACTIVE"]
        ).first()
        if existing:
            return Response({"error": "A request or grant already exists for this patient.",
                             "grant": serialize_grant(existing)},
                            status=status.HTTP_409_CONFLICT)

        grant = ConsentGrant.objects.create(
            id=new_id(),
            patient=patient,
            doctor=request.user,
            scope=_parse_scope(data.get("scope")),
            purpose=(data.get("purpose") or "")[:255] or None,
            status="PENDING",
            expires_at=timezone.now() + timedelta(days=int(data.get("durationDays") or 90)),
        )
        _notify(
            patient,
            type="CONSENT_REQUEST",
            title="A doctor has requested access",
            body=f"{request.user.name} requested access to: {', '.join(grant.scope)}.",
            link="/consent",
        )
        record_audit(action="CONSENT_REQUEST", request=request, actor=request.user,
                     resource_type="consent_grant", resource_id=grant.id,
                     metadata={"patientId": patient.id, "scope": grant.scope})
        return Response(serialize_grant(grant), status=status.HTTP_201_CREATED)


class ConsentGrantAPI(APIView):
    """Patient grants access directly to a doctor."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def post(self, request):
        data = request.data
        doctor_id = data.get("doctorId") or ""
        try:
            doctor = User.objects.get(pk=doctor_id, role=ROLE_DOCTOR, is_active=True)
        except User.DoesNotExist:
            return Response({"error": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

        grant = ConsentGrant.objects.create(
            id=new_id(),
            patient=request.user,
            doctor=doctor,
            scope=_parse_scope(data.get("scope")),
            purpose=(data.get("purpose") or "")[:255] or None,
            status="ACTIVE",
            granted_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=int(data.get("durationDays") or 90)),
        )
        _notify(
            doctor,
            type="CONSENT_GRANTED",
            title="A patient granted you access",
            body=f"{request.user.name} granted access to: {', '.join(grant.scope)}.",
            link="/doctor",
        )
        record_audit(action="CONSENT_GRANT", request=request, actor=request.user,
                     resource_type="consent_grant", resource_id=grant.id,
                     metadata={"doctorId": doctor.id, "scope": grant.scope})
        return Response(serialize_grant(grant), status=status.HTTP_201_CREATED)


class ConsentDecisionAPI(APIView):
    """Patient accepts or rejects a pending request (step 3-4)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def post(self, request, grant_id):
        try:
            grant = ConsentGrant.objects.get(pk=grant_id, patient=request.user, status="PENDING")
        except ConsentGrant.DoesNotExist:
            return Response({"error": "No pending request found."}, status=status.HTTP_404_NOT_FOUND)

        decision = (request.data.get("decision") or "").upper()
        if decision not in {"GRANT", "REJECT"}:
            return Response({"error": "Decision must be GRANT or REJECT."},
                            status=status.HTTP_400_BAD_REQUEST)

        if decision == "GRANT":
            grant.status = "ACTIVE"
            grant.granted_at = timezone.now()
            grant.scope = _parse_scope(request.data.get("scope") or grant.scope)
            if request.data.get("durationDays"):
                grant.expires_at = timezone.now() + timedelta(days=int(request.data["durationDays"]))
            _notify(
                grant.doctor,
                type="CONSENT_GRANTED",
                title="Access request approved",
                body=f"{request.user.name} approved your access request.",
                link="/doctor",
            )
        else:
            grant.status = "REJECTED"
            _notify(
                grant.doctor,
                type="CONSENT_REJECTED",
                title="Access request declined",
                body=f"{request.user.name} declined your access request.",
                link="/doctor",
            )
        grant.save()

        record_audit(action="CONSENT_DECISION", request=request, actor=request.user,
                     resource_type="consent_grant", resource_id=grant.id,
                     metadata={"decision": decision, "scope": grant.scope})
        return Response(serialize_grant(grant))


class ConsentRevokeAPI(APIView):
    """Patient revokes an active grant (step 6-7)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def post(self, request, grant_id):
        try:
            grant = ConsentGrant.objects.get(pk=grant_id, patient=request.user, status="ACTIVE")
        except ConsentGrant.DoesNotExist:
            return Response({"error": "No active grant found."}, status=status.HTTP_404_NOT_FOUND)

        grant.status = "REVOKED"
        grant.revoked_at = timezone.now()
        grant.save(update_fields=["status", "revoked_at", "updated_at"])

        _notify(
            grant.doctor,
            type="CONSENT_REVOKED",
            title="Access was revoked",
            body=f"{request.user.name} revoked your access. Future requests will be blocked.",
            link="/doctor",
        )
        record_audit(action="CONSENT_REVOKE", request=request, actor=request.user,
                     resource_type="consent_grant", resource_id=grant.id,
                     metadata={"doctorId": grant.doctor_id})
        return Response(serialize_grant(grant))
