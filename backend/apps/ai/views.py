"""Assistant, recommendations, safety evaluation and content analysis."""
import logging
import os
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai import recommendations, safety
from apps.ai.content import analyse_image
from apps.ai.engine import answer_question
from apps.ai.models import AiInteraction, Recommendation
from apps.ops.models import DeepfakeAnalysis
from apps.accounts.models import ROLE_DOCTOR, ROLE_PATIENT
from apps.connect.models import Conversation
from apps.core.permissions import ROLE_ADMIN, require_roles
from apps.core.serialize import iso, num
from apps.core.utils import new_id, record_audit

logger = logging.getLogger(__name__)


def _ai_conversation(user):
    conversation = (
        Conversation.objects.filter(patient=user, channel="PATIENT_AI")
        .order_by("-updated_at")
        .first()
    )
    if conversation is None:
        conversation = Conversation.objects.create(
            id=new_id(), patient=user, channel="PATIENT_AI", title="AI assistant"
        )
    return conversation


def serialize_message(message) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "body": message.body,
        "senderId": message.sender_id,
        "createdAt": iso(message.created_at),
        "metadata": message.metadata or {},
    }


class ChatAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = (request.data.get("message") or "").strip()
        if not message:
            return Response({"error": "Type a question to continue."},
                            status=status.HTTP_400_BAD_REQUEST)
        if len(message) > 2000:
            return Response({"error": "Please keep questions under 2000 characters."},
                            status=status.HTTP_400_BAD_REQUEST)

        conversation = None
        if request.user.role == ROLE_PATIENT:
            conversation = _ai_conversation(request.user)

        language = getattr(request.user, "language", "en") or "en"
        record_audit(action="AI_CHAT_REQUEST", request=request, actor=request.user,
                     resource_type="ai_interaction")
        return Response(answer_question(user=request.user, message=message,
                                        conversation=conversation, language=language))


class AiConversationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        conversations = Conversation.objects.filter(patient=request.user, channel="PATIENT_AI")
        return Response(
            {
                "results": [
                    {
                        "id": c.id,
                        "title": c.title or "AI assistant",
                        "updatedAt": iso(c.updated_at),
                        "messageCount": c.messages.count(),
                    }
                    for c in conversations
                ]
            }
        )


class AiConversationDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, conversation_id):
        try:
            return Conversation.objects.get(pk=conversation_id, patient=request.user,
                                            channel="PATIENT_AI")
        except Conversation.DoesNotExist:
            raise Http404

    def get(self, request, conversation_id):
        conversation = self._get(request, conversation_id)
        return Response(
            {
                "id": conversation.id,
                "title": conversation.title,
                "messages": [serialize_message(m) for m in conversation.messages.all()[:200]],
            }
        )

    def delete(self, request, conversation_id):
        conversation = self._get(request, conversation_id)
        record_audit(action="AI_HISTORY_DELETE", request=request, actor=request.user,
                     resource_type="conversation", resource_id=conversation.id)
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def describe_basis(basis) -> str:
    """Turn the internal basis object into a short, human-readable explanation."""
    if not isinstance(basis, dict):
        return ""
    parts = []
    if basis.get("condition"):
        parts.append(f"Related to your record: {basis['condition']}")
    if basis.get("flag"):
        parts.append(f"A recent measurement was flagged {str(basis['flag']).lower()}")
    if basis.get("medicationCount") is not None:
        parts.append(f"Based on {basis['medicationCount']} active medications")
    if basis.get("unverifiedCount") is not None:
        parts.append(f"{basis['unverifiedCount']} record(s) still need confirmation")
    return " · ".join(parts)


class RecommendationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        recommendations.refresh_for_patient(request.user)
        items = request.user.recommendations.filter(status="ACTIVE")
        return Response(
            {
                "results": [
                    {
                        "id": r.id,
                        "type": r.type,
                        "title": r.title,
                        "body": r.body or "",
                        "basis": r.basis or {},
                        "basisText": describe_basis(r.basis),
                        "status": r.status,
                        "createdAt": iso(r.created_at),
                    }
                    for r in items
                ]
            }
        )


class RecommendationFeedbackAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def post(self, request, recommendation_id):
        try:
            item = Recommendation.objects.get(pk=recommendation_id, user=request.user)
        except Recommendation.DoesNotExist:
            raise Http404

        next_status = (request.data.get("status") or "").upper()
        if next_status not in {"ACCEPTED", "DISMISSED"}:
            return Response({"error": "Status must be ACCEPTED or DISMISSED."},
                            status=status.HTTP_400_BAD_REQUEST)
        item.status = next_status
        item.responded_at = timezone.now()
        item.save(update_fields=["status", "responded_at"])
        record_audit(action="RECOMMENDATION_FEEDBACK", request=request, actor=request.user,
                     resource_type="recommendation", resource_id=item.id,
                     metadata={"status": next_status})
        return Response({"id": item.id, "status": item.status})


class SafetyEvaluateAPI(APIView):
    """Standalone safety evaluation of a draft answer (PRD §22)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR, ROLE_ADMIN)
    def post(self, request):
        draft = (request.data.get("answer") or "").strip()
        if not draft:
            return Response({"error": "Provide the answer text to evaluate."},
                            status=status.HTTP_400_BAD_REQUEST)
        report = safety.evaluate(answer=draft, risk_category="NORMAL")
        return Response(report.as_dict())


class ContentAnalysisAPI(APIView):
    """Experimental synthetic-content analysis (PRD §16)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"error": "Choose an image to analyse."},
                            status=status.HTTP_400_BAD_REQUEST)
        suffix = Path(upload.name or "").suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg"}:
            return Response({"error": "Only PNG and JPG images are supported."},
                            status=status.HTTP_400_BAD_REQUEST)

        relative = Path("analysis") / f"{new_id()}{suffix}"
        target = Path(settings.MEDIA_ROOT) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb+") as destination:
            for chunk in upload.chunks():
                destination.write(chunk)

        try:
            result = analyse_image(target)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("content analysis failed: %s", exc)
            os.remove(target)
            return Response({"error": "This file could not be analysed."},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        analysis = DeepfakeAnalysis.objects.create(
            id=new_id(),
            owner=request.user,
            file_name=(upload.name or "")[:255],
            mime_type=upload.content_type or "image/png",
            storage_path=str(relative),
            modality="IMAGE",
            model_version=result["detectorVersion"],
            result=result,
            risk_level=result["riskLevel"],
            uncertainty=result["uncertainty"],
            limitations=result["limitations"],
        )
        record_audit(action="CONTENT_ANALYSIS", request=request, actor=request.user,
                     resource_type="deepfake_analysis", resource_id=analysis.id,
                     metadata={"risk": result["riskLevel"]})
        return Response(
            {
                "id": analysis.id,
                "riskLevel": analysis.risk_level,
                "uncertainty": num(analysis.uncertainty),
                "indicators": result["indicators"],
                "limitations": result["limitations"],
                "detectorVersion": result["detectorVersion"],
                "experimental": True,
                "createdAt": iso(analysis.created_at),
            },
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        items = DeepfakeAnalysis.objects.filter(owner=request.user)[:20]
        return Response(
            {
                "results": [
                    {
                        "id": a.id,
                        "fileName": a.file_name,
                        "riskLevel": a.risk_level,
                        "uncertainty": num(a.uncertainty),
                        "indicators": (a.result or {}).get("indicators", []),
                        "limitations": a.limitations,
                        "createdAt": iso(a.created_at),
                    }
                    for a in items
                ]
            }
        )


class AiHistoryAPI(APIView):
    """Recent AI interactions for the signed-in user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = AiInteraction.objects.filter(user=request.user)[:20]
        return Response(
            {
                "results": [
                    {
                        "id": i.id,
                        "prompt": i.prompt,
                        "intent": i.intent,
                        "riskCategory": i.risk_category,
                        "trustScore": num(i.trust_score),
                        "model": i.model_name,
                        "createdAt": iso(i.created_at),
                    }
                    for i in items
                ]
            }
        )
