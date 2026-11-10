"""Intent detection and risk classification (PRD §12.1, §13).

A transparent rule/keyword classifier. It is deliberately inspectable: the
detectable intents are declared here, and every classification reports which
signals matched so the result can be audited and compared against a labelled
test set later (PRD §13.2).
"""
import re
from dataclasses import dataclass, field
from typing import List

URGENT_PATTERNS = [
    r"\bchest pain\b", r"\bcan'?t breathe\b", r"\bshort(ness)? of breath\b",
    r"\bdifficulty breathing\b", r"\bsevere bleeding\b", r"\bunconscious\b",
    r"\bstroke\b", r"\bheart attack\b", r"\banaphyla\w+\b", r"\bsuicid\w+\b",
    r"\bkill myself\b", r"\boverdos\w+\b", r"\bseizure\b", r"\bcall 911\b",
    r"\bemergency\b", r"\bfaint(ed|ing)?\b", r"\bnumbness on one side\b",
    r"\b胸痛\b", r"\b呼吸困难\b", r"\b昏迷\b", r"\b中风\b", r"\b急救\b",
]

OUT_OF_SCOPE_PATTERNS = [
    r"\bprescribe\b", r"\bdosage for me\b", r"\bhow much .* should i take\b",
    r"\bstop taking my\b", r"\bincrease my dose\b", r"\bdiagnose me\b",
    r"\bdo i have\b", r"\bam i going to die\b", r"\bsecond opinion on my scan\b",
    r"\bwrite me a prescription\b", r"\b给我开药\b", r"\b确诊\b",
]

# (intent, patterns) — first matching group wins for the primary intent.
INTENT_RULES = [
    ("SUMMARIZE_RECORD", [
        r"\bsummar\w+\b", r"\bsummary\b", r"\bwhat does my report say\b",
        r"\bexplain my (report|document|result)", r"\b总结\b", r"\b解读.{0,4}报告\b",
    ]),
    ("EXPLAIN_TERM", [
        r"\bwhat (is|are|does)\b", r"\bwhat does .{0,30} mean\b", r"\bdefine\b",
        r"\bmeaning of\b", r"\bterminology\b", r"\b是什么意思\b", r"\b什么意思\b",
    ]),
    ("MEDICATION_INFO", [
        r"\bmedication\b", r"\bmedicine\b", r"\bdrug\b", r"\btablet\b", r"\bdose\b",
        r"\bside effect\b", r"\b药\b", r"\b药物\b",
    ]),
    ("LAB_RESULT", [
        r"\blab\b", r"\bblood test\b", r"\bcholesterol\b", r"\bglucose\b",
        r"\bhemoglobin\b", r"\bhba1c\b", r"\breference range\b", r"\b验血\b", r"\b指标\b",
    ]),
    ("SYMPTOM_INFO", [
        r"\bsymptom\b", r"\bpain\b", r"\bfever\b", r"\bcough\b", r"\bheadache\b",
        r"\b症状\b", r"\b疼\b",
    ]),
    ("TWIN_LOOKUP", [
        r"\bmy (record|data|twin|history|allerg|medication)", r"\bdo i have any\b",
        r"\bwhen (was|did) i\b", r"\b我的\b",
    ]),
    ("NEXT_STEP", [
        r"\bwhat should i do\b", r"\bnext step\b", r"\bshould i see\b",
        r"\bwho should i (see|ask)\b", r"\b怎么办\b",
    ]),
    ("GENERAL_INFO", [
        r"\bhow (does|do|can)\b", r"\bwhy\b", r"\bprevent\b", r"\bhealthy\b",
    ]),
]

ESCALATION_TEXT = (
    "This looks like it could be urgent. MedTwin AI cannot assess emergencies. "
    "Contact your local emergency number (for example 911 / 120) or a qualified "
    "healthcare professional immediately."
)
ESCALATION_TEXT_ZH = (
    "这看起来可能属于紧急情况。MedTwin AI 无法评估紧急状况，"
    "请立即联系当地急救电话（如 911 / 120）或专业医疗人员。"
)


@dataclass
class IntentResult:
    intent: str = "GENERAL_INFO"
    risk_category: str = "NORMAL"
    signals: List[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification: str = ""


def _matches(patterns, text: str) -> List[str]:
    hits = []
    for pattern in patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append(pattern)
    return hits


def classify(message: str) -> IntentResult:
    """Classify a user message into an intent and a risk category."""
    text = (message or "").strip()
    lowered = text.lower()
    result = IntentResult()

    urgent = _matches(URGENT_PATTERNS, lowered)
    if urgent:
        result.risk_category = "URGENT"
        result.intent = "ESCALATION"
        result.signals = urgent[:5]
        return result

    out_of_scope = _matches(OUT_OF_SCOPE_PATTERNS, lowered)
    if out_of_scope:
        result.risk_category = "OUT_OF_SCOPE"
        result.signals = out_of_scope[:5]

    for intent, patterns in INTENT_RULES:
        hits = _matches(patterns, lowered)
        if hits:
            result.intent = intent
            result.signals = hits[:5]
            break

    if result.risk_category == "NORMAL" and result.intent in {"SYMPTOM_INFO", "MEDICATION_INFO"}:
        result.risk_category = "SENSITIVE"

    # Asking for clarification: short, vague requests without an object.
    if len(text.split()) <= 2 and result.intent == "GENERAL_INFO":
        result.needs_clarification = True
        result.clarification = (
            "Could you add a little more detail — for example which symptom, "
            "medication or document you mean?"
        )

    return result
