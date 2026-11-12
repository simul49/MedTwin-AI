"""MedTwin AI microservice.

This process owns *only* the AI/LLM layer: intent classification, retrieval,
generation, safety scoring, recommendations, image heuristics and document NLP.
Spring Boot owns authentication, RBAC, consent, SQL and the public HTTP contract.

The service reuses the existing Django model definitions as a plain ORM (no
Django HTTP server, no django.contrib.auth middleware), so all AI logic and
audit logging stay in one place and keep writing to the same MySQL database.
"""
from __future__ import annotations

import logging
import os
import secrets
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import close_old_connections  # noqa: E402
from django.utils import timezone  # noqa: E402
from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from apps.accounts.models import User  # noqa: E402
from apps.ai import providers, recommendations, safety  # noqa: E402
from apps.ai.content import analyse_image  # noqa: E402
from apps.ai.engine import answer_question  # noqa: E402
from apps.ai.models import AiInteraction, Recommendation  # noqa: E402
from apps.connect.models import Conversation, Message  # noqa: E402
from apps.core.serialize import iso, num  # noqa: E402
from apps.core.utils import new_id, record_audit  # noqa: E402
from apps.ops.models import DeepfakeAnalysis  # noqa: E402
from apps.twin import extraction  # noqa: E402

logger = logging.getLogger("medtwin.ai")

app = FastAPI(title="MedTwin AI service", version="1.0.0")


@app.middleware("http")
async def manage_db_connections(request: Request, call_next):
    close_old_connections()
    try:
        return await call_next(request)
    finally:
        close_old_connections()


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail)})


def _verify_secret(request: Request) -> None:
    expected = os.environ.get("MEDTWIN_AI_SHARED_SECRET", "")
    if expected and not secrets.compare_digest(
        request.headers.get("X-Medtwin-AI-Secret", ""), expected
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


def _actor(request: Request) -> User:
    _verify_secret(request)
    user_id = request.headers.get("X-Medtwin-User-Id", "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = User.objects.filter(pk=user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user


def _ai_conversation(user: User) -> Conversation:
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


def _serialize_message(message: Message) -> Dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "body": message.body,
        "senderId": message.sender_id,
        "createdAt": iso(message.created_at),
        "metadata": message.metadata or {},
    }


def _describe_basis(basis: Any) -> str:
    if not isinstance(basis, dict):
        return ""
    parts: List[str] = []
    if basis.get("condition"):
        parts.append(f"Related to your record: {basis['condition']}")
    if basis.get("flag"):
        parts.append(f"A recent measurement was flagged {str(basis['flag']).lower()}")
    if basis.get("medicationCount") is not None:
        parts.append(f"Based on {basis['medicationCount']} active medications")
    if basis.get("unverifiedCount") is not None:
        parts.append(f"{basis['unverifiedCount']} record(s) still need confirmation")
    return " · ".join(parts)


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------
@app.post("/ai/chat/")
def chat(request: Request, payload: Dict[str, Any] = Body(default={})):
    user = _actor(request)
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Type a question to continue.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Please keep questions under 2000 characters.")

    conversation = _ai_conversation(user) if user.role == "PATIENT" else None
    record_audit(action="AI_CHAT_REQUEST", actor=user, resource_type="ai_interaction")
    result = answer_question(
        user=user,
        message=message,
        conversation=conversation,
        language=getattr(user, "language", "en") or "en",
    )
    if conversation is not None:
        Conversation.objects.filter(pk=conversation.pk).update(updated_at=timezone.now())
    return result


# ---------------------------------------------------------------------------
# Public website chatbot (anonymous, rate-limited, same safety pipeline)
# ---------------------------------------------------------------------------
_PUBLIC_HITS: Dict[str, List[float]] = {}
_PUBLIC_RATE_LIMIT = 20
_PUBLIC_RATE_WINDOW = 300.0


def _public_rate_limit(request: Request) -> None:
    forwarded = request.headers.get("x-forwarded-for", "")
    key = forwarded.split(",")[0].strip() if forwarded else (
        request.client.host if request.client else "unknown"
    )
    now = time.time()
    hits = [t for t in _PUBLIC_HITS.get(key, []) if now - t < _PUBLIC_RATE_WINDOW]
    if len(hits) >= _PUBLIC_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests — please try again shortly.")
    hits.append(now)
    _PUBLIC_HITS[key] = hits


@app.post("/public-chat/")
def public_chat(request: Request, payload: Dict[str, Any] = Body(default={})):
    """Anonymous general-health Q&A for the public website.

    Runs the same intent → retrieval → generation → safety pipeline as the
    patient assistant, but with no patient context and no conversation history.
    """
    _verify_secret(request)
    _public_rate_limit(request)
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Type a question to continue.")
    if len(message) > 1000:
        raise HTTPException(status_code=400, detail="Please keep questions under 1000 characters.")
    language = payload.get("language")
    result = answer_question(
        user=None,
        message=message,
        conversation=None,
        language=language if language in {"en", "zh"} else "en",
    )
    return {
        "answer": result["answer"],
        "intent": result["intent"],
        "sources": result["sources"],
        "limitations": result["limitations"],
        "nextStep": result["nextStep"],
        "safety": result["safety"],
        "model": result["model"],
    }


@app.get("/ai/conversations/")
def ai_conversations(request: Request):
    user = _actor(request)
    rows = Conversation.objects.filter(patient=user, channel="PATIENT_AI")
    return {
        "results": [
            {
                "id": c.id,
                "title": c.title or "AI assistant",
                "updatedAt": iso(c.updated_at),
                "messageCount": c.messages.count(),
            }
            for c in rows
        ]
    }


@app.get("/ai/conversations/{conversation_id}/")
def ai_conversation_detail(conversation_id: str, request: Request):
    user = _actor(request)
    conversation = Conversation.objects.filter(
        pk=conversation_id, patient=user, channel="PATIENT_AI"
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Not found.")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [_serialize_message(m) for m in conversation.messages.all()[:200]],
    }


@app.delete("/ai/conversations/{conversation_id}/")
def ai_conversation_delete(conversation_id: str, request: Request):
    user = _actor(request)
    conversation = Conversation.objects.filter(
        pk=conversation_id, patient=user, channel="PATIENT_AI"
    ).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Not found.")
    record_audit(
        action="AI_HISTORY_DELETE", actor=user,
        resource_type="conversation", resource_id=conversation.id,
    )
    conversation.delete()
    return {"ok": True}


@app.get("/ai/history/")
def ai_history(request: Request):
    user = _actor(request)
    return {
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
            for i in AiInteraction.objects.filter(user=user)[:20]
        ]
    }


# ---------------------------------------------------------------------------
# Recommendations and safety
# ---------------------------------------------------------------------------
@app.get("/recommendations/")
def recommendation_list(request: Request):
    user = _actor(request)
    recommendations.refresh_for_patient(user)
    return {
        "results": [
            {
                "id": r.id,
                "type": r.type,
                "title": r.title,
                "body": r.body or "",
                "basis": r.basis or {},
                "basisText": _describe_basis(r.basis),
                "status": r.status,
                "createdAt": iso(r.created_at),
            }
            for r in user.recommendations.filter(status="ACTIVE")
        ]
    }


@app.post("/recommendations/{recommendation_id}/feedback/")
def recommendation_feedback(recommendation_id: str, request: Request,
                            payload: Dict[str, Any] = Body(default={})):
    user = _actor(request)
    item = Recommendation.objects.filter(pk=recommendation_id, user=user).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Not found.")
    status = (payload.get("status") or "").upper()
    if status not in {"ACCEPTED", "DISMISSED"}:
        raise HTTPException(status_code=400, detail="Status must be ACCEPTED or DISMISSED.")
    item.status = status
    item.responded_at = timezone.now()
    item.save(update_fields=["status", "responded_at"])
    record_audit(
        action="RECOMMENDATION_FEEDBACK", actor=user,
        resource_type="recommendation", resource_id=item.id,
        metadata={"status": status},
    )
    return {"id": item.id, "status": item.status}


@app.post("/safety/evaluate/")
def evaluate_safety(request: Request, payload: Dict[str, Any] = Body(default={})):
    _actor(request)
    draft = (payload.get("answer") or "").strip()
    if not draft:
        raise HTTPException(status_code=400, detail="Provide the answer text to evaluate.")
    return safety.evaluate(answer=draft, risk_category="NORMAL").as_dict()


# ---------------------------------------------------------------------------
# Experimental synthetic-content analysis
# ---------------------------------------------------------------------------
@app.get("/content-analysis/")
def content_analysis_list(request: Request):
    user = _actor(request)
    return {
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
            for a in DeepfakeAnalysis.objects.filter(owner=user)[:20]
        ]
    }


@app.post("/content-analysis/")
def content_analysis_create(request: Request, file: UploadFile = File(...)):
    # Sync endpoint (threadpool) so the Django ORM calls below are allowed.
    user = _actor(request)
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Only PNG and JPG images are supported.")

    relative = Path("analysis") / f"{new_id()}{suffix}"
    target = Path(settings.MEDIA_ROOT) / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    file.file.seek(0)
    target.write_bytes(file.file.read())
    try:
        result = analyse_image(target)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("content analysis failed: %s", exc)
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="This file could not be analysed.")

    analysis = DeepfakeAnalysis.objects.create(
        id=new_id(),
        owner=user,
        file_name=(file.filename or "")[:255],
        mime_type=file.content_type or "image/png",
        storage_path=str(relative),
        modality="IMAGE",
        model_version=result["detectorVersion"],
        result=result,
        risk_level=result["riskLevel"],
        uncertainty=result["uncertainty"],
        limitations=result["limitations"],
    )
    record_audit(
        action="CONTENT_ANALYSIS", actor=user,
        resource_type="deepfake_analysis", resource_id=analysis.id,
        metadata={"risk": result["riskLevel"]},
    )
    return {
        "id": analysis.id,
        "riskLevel": analysis.risk_level,
        "uncertainty": num(analysis.uncertainty),
        "indicators": result["indicators"],
        "limitations": result["limitations"],
        "detectorVersion": result["detectorVersion"],
        "experimental": True,
        "createdAt": iso(analysis.created_at),
    }


# ---------------------------------------------------------------------------
# Internal endpoints called by Spring only (no user-facing data)
# ---------------------------------------------------------------------------
@app.get("/health/")
def health():
    return {"service": "medtwin-ai-python", "version": "1.0.0", "status": "ok"}


@app.get("/internal/model/")
def internal_model(request: Request):
    _verify_secret(request)
    return providers.active_model()


@app.post("/internal/extract/")
def internal_extract(request: Request, payload: Dict[str, Any] = Body(default={})):
    """Document NLP (PDF text layer + candidate fields) for Spring's upload flow."""
    _verify_secret(request)
    media_root = Path(settings.MEDIA_ROOT).resolve()
    path = Path(str(payload.get("path") or "")).resolve()
    if media_root not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid document path.")
    if not path.is_file():
        raise HTTPException(status_code=400, detail="Document not found.")

    mime = str(payload.get("mimeType") or "")
    text, page_count, error = extraction.extract_text(path, mime)
    return {
        "text": text,
        "pageCount": page_count,
        "error": error,
        "fields": extraction.derive_fields(text),
        "sha256": extraction.sha256_of(path),
    }
