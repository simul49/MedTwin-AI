"""Orchestration of one assistant turn (PRD §12.1).

Pipeline: intent → retrieve → patient context → generate/compose →
safety evaluation → persist. Safety always runs before anything is returned,
and every stage is recorded so a trace can be inspected later.
"""
import logging
import time
from typing import Dict, List, Optional

from apps.ai import composer, providers, retrieval, safety
from apps.ai.intent import classify
from apps.ai.models import AiInteraction
from apps.ai.providers import ProviderUnavailable
from apps.core.utils import new_id, record_audit, trace_id

logger = logging.getLogger(__name__)

INTENT_CONTEXT_MAP = {
    "MEDICATION_INFO": ["medications", "allergies"],
    "LAB_RESULT": ["lab_results"],
    "SYMPTOM_INFO": ["conditions", "allergies"],
    "TWIN_LOOKUP": ["conditions", "medications", "allergies", "lab_results"],
    "SUMMARIZE_RECORD": ["lab_results"],
    "EXPLAIN_TERM": ["conditions"],
    "NEXT_STEP": ["conditions", "medications"],
    "GENERAL_INFO": ["conditions"],
    "ESCALATION": [],
}


def _context_categories(intent: str) -> List[str]:
    return INTENT_CONTEXT_MAP.get(intent, ["conditions"])


def answer_question(*, user, message: str, conversation=None, language: str = "en") -> Dict:
    started = time.time()
    trace = trace_id()

    intent_result = classify(message)
    clinical = getattr(user, "role", "") == "DOCTOR"
    passages = retrieval.retrieve(message, top_k=5, clinical=clinical)

    twin_context: Dict[str, list] = {}
    if getattr(user, "role", "") == "PATIENT" and intent_result.risk_category == "NORMAL":
        twin_context = retrieval.build_twin_context(user, _context_categories(intent_result.intent))

    passage_dicts = [p.as_citation(i) for i, p in enumerate(passages, start=1)]

    composed = composer.compose(
        message=message,
        intent=intent_result.intent,
        risk_category=intent_result.risk_category,
        passages=passages,
        twin_context=twin_context,
        language=language,
    )

    model = providers.active_model()
    answer_text = composed["answer"]
    generation_mode = "offline_composer"

    if providers.is_configured():
        try:
            generated = providers.generate(
                system=providers.SYSTEM_PROMPT,
                user=providers.build_user_prompt(
                    message=message, passages=passage_dicts, twin_context=twin_context
                ),
                passages=passage_dicts,
            )
            if generated:
                answer_text = generated
                generation_mode = "provider"
        except ProviderUnavailable as exc:
            logger.warning("falling back to offline composer: %s", exc)
            composed["limitations"].append(
                "The configured AI provider was unavailable; this answer came from the "
                "built-in offline engine."
            )

    report = safety.evaluate(
        answer=answer_text,
        passages=passages,
        twin_context=twin_context,
        risk_category=intent_result.risk_category,
        intent=intent_result.intent,
        escalation=intent_result.risk_category == "URGENT",
    )

    latency_ms = int((time.time() - started) * 1000)

    interaction = AiInteraction.objects.create(
        id=new_id(),
        user=user if getattr(user, "is_authenticated", False) else None,
        conversation_id=getattr(conversation, "id", None),
        request_type="CHAT",
        prompt=message[:4000],
        answer=answer_text[:8000],
        intent=intent_result.intent,
        risk_category=intent_result.risk_category,
        model_name=model["name"],
        model_version=f"{model['version']}:{generation_mode}",
        sources=passage_dicts,
        safety=report.as_dict(),
        trust_score=safety.score_to_decimal(report.score),
        latency_ms=latency_ms,
        trace_id=trace,
    )

    if conversation is not None:
        from apps.connect.models import Message

        Message.objects.create(
            id=new_id(), conversation=conversation, sender=user, role="USER", body=message[:4000]
        )
        Message.objects.create(
            id=new_id(),
            conversation=conversation,
            sender=None,
            role="AI",
            body=answer_text[:8000],
            metadata={
                "interactionId": interaction.id,
                "sources": passage_dicts,
                "safety": report.as_dict(),
                "intent": intent_result.intent,
            },
        )

    record_audit(
        action="AI_CHAT",
        actor=user,
        resource_type="ai_interaction",
        resource_id=interaction.id,
        metadata={"intent": intent_result.intent, "risk": intent_result.risk_category, "traceId": trace},
    )

    return {
        "interactionId": interaction.id,
        "traceId": trace,
        "answer": answer_text,
        "intent": intent_result.intent,
        "riskCategory": intent_result.risk_category,
        "contextUsed": composed["contextUsed"],
        "sources": passage_dicts,
        "limitations": composed["limitations"],
        "nextStep": composed["nextStep"],
        "needsClarification": intent_result.needs_clarification,
        "clarification": intent_result.clarification,
        "safety": report.as_dict(),
        "model": {**model, "generationMode": generation_mode, "latencyMs": latency_ms},
    }
