"""Health, administration, governance and audit review (PRD §19.3, §23)."""
import logging
from datetime import timedelta

from django.db import connection
from django.db.utils import DatabaseError, OperationalError
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ROLE_ADMIN, User
from apps.accounts.serializers import serialize_user
from apps.ai import providers
from apps.ai.models import AiInteraction, KnowledgeChunk, KnowledgeSource
from apps.ops.models import AuditLog, FeatureFlag, ModelVersion
from apps.consent.models import ConsentGrant
from apps.consent.serializers import serialize_grant
from apps.core.permissions import require_roles
from apps.core.serialize import iso
from apps.core.utils import new_id, record_audit
from apps.ops.models import AuditLog, FeatureFlag

logger = logging.getLogger(__name__)


def serialize_source(source) -> dict:
    return {
        "id": source.id,
        "title": source.title,
        "publisher": source.publisher or "",
        "version": source.version or "",
        "sourceUrl": source.source_url or "",
        "category": source.category or "",
        "licenseStatus": source.license_status,
        "reviewStatus": source.review_status,
        "ingestedAt": iso(source.ingested_at),
        "chunkCount": source.chunks.count(),
        "createdAt": iso(source.created_at),
    }


def serialize_audit(entry) -> dict:
    return {
        "id": entry.id,
        "actorId": entry.actor_id,
        "actorEmail": entry.actor_email or "",
        "action": entry.action,
        "resourceType": entry.resource_type or "",
        "resourceId": entry.resource_id or "",
        "outcome": entry.outcome,
        "ipAddress": entry.ip_address or "",
        "traceId": entry.trace_id or "",
        "metadata": entry.metadata or {},
        "createdAt": iso(entry.created_at),
    }


class HealthAPI(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database = "ok"
        except (OperationalError, DatabaseError) as exc:
            database = f"unavailable: {exc}"

        return Response(
            {
                "service": "medtwin-django",
                "version": "1.0.0",
                "database": database,
                "aiProvider": providers.active_model(),
                "time": iso(timezone.now()),
            }
        )


class AdminUserListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_ADMIN)
    def get(self, request):
        role = request.query_params.get("role") or ""
        query = (request.query_params.get("q") or "").strip()
        users = User.objects.all()
        if role:
            users = users.filter(role=role.upper())
        if query:
            users = users.filter(name__icontains=query) | users.filter(email__icontains=query)
        record_audit(action="ADMIN_USER_LIST", request=request, actor=request.user,
                     resource_type="user")
        return Response({"results": [serialize_user(u) for u in users[:200]]})


class AdminUserDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404

    @require_roles(ROLE_ADMIN)
    def patch(self, request, user_id):
        user = self._get(user_id)
        data = request.data
        changed = []
        if "isActive" in data:
            user.is_active = bool(data["isActive"])
            changed.append("isActive")
        if "isVerified" in data:
            user.is_verified = bool(data["isVerified"])
            changed.append("isVerified")
        if "role" in data and data["role"] in {"PATIENT", "DOCTOR", "ADMIN"}:
            user.role = data["role"]
            changed.append("role")
        if changed:
            user.save()

        doctor_profile = getattr(user, "doctor_profile", None)
        if doctor_profile is not None and "verificationStatus" in data:
            doctor_profile.verification_status = data["verificationStatus"]
            if data["verificationStatus"] == "VERIFIED":
                doctor_profile.verified_at = timezone.now()
            doctor_profile.save()
            changed.append("verificationStatus")

        record_audit(action="ADMIN_USER_UPDATE", request=request, actor=request.user,
                     resource_type="user", resource_id=user.id, metadata={"fields": changed})
        return Response(serialize_user(user))


class AdminAuditLogAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_ADMIN)
    def get(self, request):
        action = request.query_params.get("action") or ""
        outcome = request.query_params.get("outcome") or ""
        actor = request.query_params.get("actor") or ""
        entries = AuditLog.objects.all()
        if action:
            entries = entries.filter(action=action)
        if outcome:
            entries = entries.filter(outcome=outcome.upper())
        if actor:
            entries = entries.filter(actor_email__icontains=actor)
        record_audit(action="AUDIT_READ", request=request, actor=request.user,
                     resource_type="audit_log", metadata={"filters": {"action": action, "outcome": outcome}})
        return Response({"results": [serialize_audit(e) for e in entries[:300]]})


class AdminConsentAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_ADMIN)
    def get(self, request):
        grants = ConsentGrant.objects.all().select_related("doctor", "patient").order_by("-created_at")[:200]
        return Response({"results": [serialize_grant(g) for g in grants]})


class KnowledgeSourceListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sources = KnowledgeSource.objects.all()
        return Response({"results": [serialize_source(s) for s in sources]})

    @require_roles(ROLE_ADMIN)
    def post(self, request):
        data = request.data
        title = (data.get("title") or "").strip()
        if not title:
            return Response({"error": "A title is required."}, status=status.HTTP_400_BAD_REQUEST)
        source = KnowledgeSource.objects.create(
            id=new_id(),
            title=title[:255],
            publisher=(data.get("publisher") or "")[:160] or None,
            version=(data.get("version") or "")[:60] or None,
            source_url=(data.get("sourceUrl") or "")[:500] or None,
            category=(data.get("category") or "")[:60] or None,
            license_status=(data.get("licenseStatus") or "UNKNOWN").upper(),
            review_status=(data.get("reviewStatus") or "PENDING").upper(),
            ingested_at=timezone.now(),
        )
        record_audit(action="KNOWLEDGE_SOURCE_CREATE", request=request, actor=request.user,
                     resource_type="knowledge_source", resource_id=source.id)
        return Response(serialize_source(source), status=status.HTTP_201_CREATED)


class KnowledgeSourceDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, source_id):
        try:
            return KnowledgeSource.objects.get(pk=source_id)
        except KnowledgeSource.DoesNotExist:
            raise Http404

    @require_roles(ROLE_ADMIN)
    def patch(self, request, source_id):
        source = self._get(source_id)
        if "reviewStatus" in request.data:
            source.review_status = request.data["reviewStatus"].upper()
        if "licenseStatus" in request.data:
            source.license_status = request.data["licenseStatus"].upper()
        source.save()
        record_audit(action="KNOWLEDGE_SOURCE_UPDATE", request=request, actor=request.user,
                     resource_type="knowledge_source", resource_id=source.id,
                     metadata={"reviewStatus": source.review_status})
        return Response(serialize_source(source))

    @require_roles(ROLE_ADMIN)
    def delete(self, request, source_id):
        source = self._get(source_id)
        record_audit(action="KNOWLEDGE_SOURCE_DELETE", request=request, actor=request.user,
                     resource_type="knowledge_source", resource_id=source.id)
        source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SystemHealthAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_ADMIN)
    def get(self, request):
        now = timezone.now()
        day_ago = now - timedelta(days=1)
        try:
            database = "ok"
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
        except (OperationalError, DatabaseError) as exc:
            database = f"unavailable: {exc}"
            user_count = 0

        record_audit(action="SYSTEM_HEALTH_READ", request=request, actor=request.user,
                     resource_type="system")
        return Response(
            {
                "database": database,
                "aiProvider": providers.active_model(),
                "counts": {
                    "users": user_count,
                    "knowledgeSources": KnowledgeSource.objects.count(),
                    "knowledgeChunks": KnowledgeChunk.objects.count(),
                    "consentGrants": ConsentGrant.objects.count(),
                    "activeGrants": ConsentGrant.objects.filter(status="ACTIVE").count(),
                    "aiInteractions": AiInteraction.objects.count(),
                    "lowTrustResponses": AiInteraction.objects.filter(trust_score__lt=60).count(),
                    "auditEvents24h": AuditLog.objects.filter(created_at__gte=day_ago).count(),
                    "deniedEvents24h": AuditLog.objects.filter(
                        created_at__gte=day_ago, outcome="DENIED"
                    ).count(),
                },
                "models": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "version": m.version,
                        "provider": m.provider or "",
                        "kind": m.kind,
                        "isActive": m.is_active,
                    }
                    for m in ModelVersion.objects.all()
                ],
                "generatedAt": iso(now),
            }
        )


class FeatureFlagListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        flags = FeatureFlag.objects.all()
        return Response(
            {
                "results": [
                    {
                        "id": f.id,
                        "key": f.flag_key,
                        "label": f.label or "",
                        "description": f.description or "",
                        "isEnabled": f.is_enabled,
                        "status": f.status,
                        "updatedAt": iso(f.updated_at),
                    }
                    for f in flags
                ]
            }
        )


class FeatureFlagDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, flag_id):
        try:
            return FeatureFlag.objects.get(pk=flag_id)
        except FeatureFlag.DoesNotExist:
            raise Http404

    @require_roles(ROLE_ADMIN)
    def patch(self, request, flag_id):
        flag = self._get(flag_id)
        if "isEnabled" in request.data:
            flag.is_enabled = bool(request.data["isEnabled"])
        if "status" in request.data:
            flag.status = request.data["status"].upper()
        flag.save()
        record_audit(action="FEATURE_FLAG_UPDATE", request=request, actor=request.user,
                     resource_type="feature_flag", resource_id=flag.id,
                     metadata={"isEnabled": flag.is_enabled, "status": flag.status})
        return Response({"id": flag.id, "isEnabled": flag.is_enabled, "status": flag.status})
