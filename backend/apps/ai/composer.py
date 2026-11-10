"""Offline response composition (PRD §11.4, §12).

When no LLM provider is configured the assistant still has to answer honestly.
The composer builds an extractive answer: every statement is drawn from a
retrieved passage or from the patient's own Digital Twin, and anything it cannot
support is stated as a limitation. No medical claim is invented.
"""
from typing import Dict, List

from apps.ai.intent import ESCALATION_TEXT, ESCALATION_TEXT_ZH
from apps.ai.retrieval import Passage

ZH = {
    "intro": "以下是我在已审核知识库中找到的内容。",
    "sources": "来源内容",
    "twin": "来自你的数字孪生（Digital Twin）",
    "limits": "这些信息不能说明什么",
    "no_source": "我没有在已审核的知识库中检索到与你问题相关的资料。",
    "disclaimer": "以上为来自已审核来源的科普信息，不是诊断结论。",
    "next": "建议：把这个问题和相关资料带给你的医生一起讨论。",
    "escalate": "这看起来可能属于紧急情况。",
    "out_of_scope": "这个问题涉及诊断、处方或调整用药，必须由具备资质的医生决定，我无法代替。",
    "no_med": "没有记录到在用的药物。",
    "no_allergy": "没有记录到过敏信息。",
    "no_lab": "没有记录到最近的检验结果。",
}


def _lead_sentences(text: str, count: int = 2) -> str:
    cleaned = " ".join((text or "").split())
    out: List[str] = []
    for part in cleaned.replace("。", ". ").split(". "):
        part = part.strip()
        if not part:
            continue
        out.append(part)
        if len(out) >= count:
            break
    lead = ". ".join(out).strip()
    return lead + "." if lead and not lead.endswith(".") else lead


def _format_twin(twin_context: Dict[str, list], language: str) -> List[str]:
    lines: List[str] = []
    meds = twin_context.get("medications") or []
    allergies = twin_context.get("allergies") or []
    labs = twin_context.get("lab_results") or []
    conditions = twin_context.get("conditions") or []

    if conditions:
        label = "Recorded conditions" if language != "zh" else "已记录的健康状况"
        lines.append(f"{label}: " + ", ".join(c["title"] for c in conditions[:5]))
    if meds:
        label = "Active medications" if language != "zh" else "在用的药物"
        lines.append(
            f"{label}: "
            + ", ".join(f"{m['name']}{' ' + m['dose'] if m.get('dose') else ''}" for m in meds[:5])
        )
    elif twin_context.get("medications") is not None:
        lines.append(ZH["no_med"] if language == "zh" else "No active medication is recorded.")
    if allergies:
        label = "Allergies on file" if language != "zh" else "已记录的过敏"
        lines.append(f"{label}: " + ", ".join(a["substance"] for a in allergies[:5]))
    if labs:
        label = "Most recent results" if language != "zh" else "最近的检验结果"
        lines.append(
            f"{label}: "
            + ", ".join(f"{l['label']} {l['value']}{(' ' + l['unit']) if l.get('unit') else ''}" for l in labs[:5])
        )
    return lines


def compose(
    *,
    message: str,
    intent: str,
    risk_category: str,
    passages: List[Passage],
    twin_context: Dict[str, list],
    language: str = "en",
) -> Dict[str, object]:
    """Return ``{answer, contextUsed, limitations, nextStep}``."""
    zh = language == "zh"

    if risk_category == "URGENT" or intent == "ESCALATION":
        return {
            "answer": (ZH["escalate"] + "\n\n" + ESCALATION_TEXT_ZH) if zh else ESCALATION_TEXT,
            "contextUsed": [],
            "limitations": [
                ZH["disclaimer"] if zh else "MedTwin AI cannot assess or manage emergencies."
            ],
            "nextStep": (ZH["next"] if zh else "Contact emergency services or your clinician now."),
        }

    if risk_category == "OUT_OF_SCOPE":
        return {
            "answer": (
                ZH["out_of_scope"]
                + "\n\n"
                + (ZH["next"] if zh else "What I can do: explain your records, explain terminology, "
                   "and help you prepare questions for your clinician.")
            ),
            "contextUsed": [],
            "limitations": [
                ZH["disclaimer"] if zh else "Diagnosis, prescribing and dose changes remain clinician decisions."
            ],
            "nextStep": ZH["next"] if zh else "Book time with your clinician to review this.",
        }

    blocks: List[str] = []
    context_used: List[str] = []

    if passages:
        lead = _lead_sentences(passages[0].text)
        attribution = passages[0].publisher or passages[0].source_title
        if zh:
            blocks.append(f"{lead}（来源：{attribution} [1]）")
        else:
            blocks.append(f"{lead} (source: {attribution} [1])")

        header = ZH["sources"] if zh else "What the sources say"
        blocks.append(header)
        for index, passage in enumerate(passages, start=1):
            excerpt = " ".join(passage.text.split())[:260]
            blocks.append(f"- [{index}] {passage.source_title} — {excerpt}")

        context_used.append(
            f"{len(passages)} passage(s) from approved knowledge sources"
            if not zh
            else f"来自已审核知识库的 {len(passages)} 段内容"
        )
    else:
        blocks.append(ZH["no_source"] if zh else "I could not find approved reference material for this question.")

    twin_lines = _format_twin(twin_context, language)
    if twin_lines:
        blocks.append(ZH["twin"] if zh else "From your Digital Twin")
        blocks.extend(f"- {line}" for line in twin_lines)
        context_used.append(
            "your Digital Twin: " + ", ".join(sorted(twin_context.keys()))
            if not zh
            else "你的数字孪生（Digital Twin）"
        )

    limitations: List[str] = []
    if not passages:
        limitations.append(
            ZH["disclaimer"] if zh else "This answer is not grounded in an approved source; treat it as unconfirmed."
        )
    else:
        limitations.append(
            ZH["disclaimer"] if zh else "Approved sources are general references; they do not know your full history."
        )
    if not twin_context:
        limitations.append(
            "No patient context was used, so this is general information."
            if not zh
            else "本次未使用你的个人健康数据，因此这是通用科普信息。"
        )
    limitations.append(
        "Extracted or AI-composed text is never a substitute for clinician review."
        if not zh
        else "自动提取或 AI 生成的内容不能替代医生审核。"
    )

    blocks.append(ZH["limits"] if zh else "Limitations")
    blocks.extend(f"- {line}" for line in limitations)
    blocks.append(ZH["disclaimer"] if zh else "General information from approved sources — not a diagnosis.")

    return {
        "answer": "\n".join(blocks),
        "contextUsed": context_used,
        "limitations": limitations,
        "nextStep": (
            ZH["next"]
            if zh
            else "Bring this summary and your questions to your next appointment."
        ),
    }
