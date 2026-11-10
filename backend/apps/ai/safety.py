"""AI Trust & Safety evaluation (PRD §15).

Produces an interpretable indicator built from named factors. It is an
evaluation aid, never a guarantee of medical correctness: the returned payload
always carries that disclaimer and the factor breakdown so a reader can see
*why* the indicator has the value it has (PRD §15.2).
"""
import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Dict, List, Optional

SAFETY_VERSION = "trust-v1.0"

# Phrases that must not appear in an assistant answer (PRD §11.2).
PROHIBITED_PATTERNS = [
    r"\byou (definitely|certainly) have\b",
    r"\byou do not have\b",
    r"\bthis is definitely\b",
    r"\btake \d+\s?(mg|ml|tablets?)\b",
    r"\bincrease your dose\b",
    r"\bstop taking\b",
    r"\bI diagnose\b",
    r"\bprescrib\w+ you\b",
    r"\bcures?\b",
    r"\bguaranteed?\b",
    r"\b100% (safe|effective)\b",
]

# Strong claims that need support before they can be shown.
UNSUPPORTED_CLAIM_PATTERNS = [
    r"\balways\b", r"\bnever\b", r"\bproven to\b", r"\bcompletely (safe|eliminates)\b",
    r"\bno risk\b", r"\bwithout any side effects\b",
]

FACTOR_WEIGHTS = {
    "source_grounding": 0.24,
    "reference_availability": 0.12,
    "context_match": 0.14,
    "contradiction_check": 0.14,
    "safety_rules": 0.20,
    "unsupported_claims": 0.10,
    "risk_routing": 0.06,
}

FACTOR_LABELS = {
    "source_grounding": "Knowledge grounding",
    "reference_availability": "Reference availability",
    "context_match": "Patient context match",
    "contradiction_check": "Contradiction check",
    "safety_rules": "Safety rules",
    "unsupported_claims": "Unsupported claims",
    "risk_routing": "Risk routing",
}


@dataclass
class Factor:
    key: str
    label: str
    status: str  # "pass" | "warn" | "fail" | "info"
    score: float  # 0..1
    detail: str


@dataclass
class SafetyReport:
    score: float
    factors: List[Factor] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    version: str = SAFETY_VERSION

    def as_dict(self) -> Dict:
        return {
            "score": round(self.score, 1),
            "version": self.version,
            "labels": self.labels,
            "factors": [
                {
                    "key": f.key,
                    "label": f.label,
                    "status": f.status,
                    "score": round(f.score, 3),
                    "weight": FACTOR_WEIGHTS[f.key],
                    "detail": f.detail,
                }
                for f in self.factors
            ],
            "disclaimer": (
                "This indicator summarises automated checks. It is an evaluation "
                "aid, not a guarantee of medical correctness."
            ),
        }


def _sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "") if s.strip()]


def evaluate(
    *,
    answer: str,
    passages: Optional[List] = None,
    twin_context: Optional[Dict] = None,
    risk_category: str = "NORMAL",
    intent: str = "GENERAL_INFO",
    escalation: bool = False,
) -> SafetyReport:
    passages = passages or []
    twin_context = twin_context or {}
    answer_l = (answer or "").lower()
    factors: List[Factor] = []
    labels: List[str] = []

    # 1. Source grounding -----------------------------------------------------
    cited = set(re.findall(r"\[(\d+)\]", answer or ""))
    if passages:
        ratio = min(1.0, len(cited) / max(1, min(len(passages), 3)))
        if ratio >= 0.6:
            factors.append(Factor("source_grounding", FACTOR_LABELS["source_grounding"], "pass", min(1.0, 0.6 + ratio * 0.4),
                                  f"Answer cites {len(cited)} of {len(passages)} retrieved passage(s)."))
        elif ratio > 0:
            factors.append(Factor("source_grounding", FACTOR_LABELS["source_grounding"], "warn", 0.5,
                                  "Only part of the answer is tied to retrieved evidence."))
        else:
            factors.append(Factor("source_grounding", FACTOR_LABELS["source_grounding"], "fail", 0.15,
                                  "No retrieved passage is cited in this answer."))
    else:
        factors.append(Factor("source_grounding", FACTOR_LABELS["source_grounding"], "info", 0.4,
                              "No knowledge passages were retrieved; the answer is not source-grounded."))

    # 2. Reference availability ----------------------------------------------
    if passages:
        factors.append(Factor("reference_availability", FACTOR_LABELS["reference_availability"], "pass", 1.0,
                              f"{len(passages)} approved reference passage(s) available."))
        labels.append("sources found")
    else:
        factors.append(Factor("reference_availability", FACTOR_LABELS["reference_availability"], "warn", 0.3,
                              "No approved reference could be retrieved for this question."))
        labels.append("no source found")

    # 3. Patient context match ------------------------------------------------
    used_context = any(
        key in answer_l for key in ("your digital twin", "your record", "your medication", "your allergy", "your result")
    )
    if twin_context and used_context:
        factors.append(Factor("context_match", FACTOR_LABELS["context_match"], "pass", 1.0,
                              "Authorised patient context was used and labelled as such."))
    elif twin_context:
        factors.append(Factor("context_match", FACTOR_LABELS["context_match"], "info", 0.6,
                              "Patient context was available but not referenced in the answer."))
        labels.append("context incomplete")
    else:
        factors.append(Factor("context_match", FACTOR_LABELS["context_match"], "info", 0.6,
                              "No patient context was required for this question."))

    # 4. Contradiction check --------------------------------------------------
    contradictions = []
    for allergy in twin_context.get("allergies", []):
        substance = (allergy.get("substance") or "").lower()
        if substance and substance in answer_l:
            contradictions.append(f"answer mentions {allergy['substance']}, which is recorded as an allergy")
    if contradictions:
        factors.append(Factor("contradiction_check", FACTOR_LABELS["contradiction_check"], "fail", 0.2,
                              "Possible conflict with the Digital Twin: " + "; ".join(contradictions)))
        labels.append("needs review")
    else:
        factors.append(Factor("contradiction_check", FACTOR_LABELS["contradiction_check"], "pass", 1.0,
                              "No conflict detected against the available patient context."))

    # 5. Safety rules ---------------------------------------------------------
    violations = [p for p in PROHIBITED_PATTERNS if re.search(p, answer_l)]
    if violations:
        factors.append(Factor("safety_rules", FACTOR_LABELS["safety_rules"], "fail", 0.0,
                              "Answer contains language reserved for clinicians "
                              f"({len(violations)} phrase(s))."))
        labels.append("blocked by safety rules")
    else:
        factors.append(Factor("safety_rules", FACTOR_LABELS["safety_rules"], "pass", 1.0,
                              "No diagnosis, prescription or dose-change language detected."))

    # 6. Unsupported claims ---------------------------------------------------
    # Only the body is scanned: the trailing "Limitations"/disclaimer block
    # legitimately uses words such as "never" and would produce false positives.
    body = re.split(r"\nLimitations\b", answer or "", maxsplit=1)[0].lower()
    unsupported = [p for p in UNSUPPORTED_CLAIM_PATTERNS if re.search(p, body)]
    if unsupported:
        factors.append(Factor("unsupported_claims", FACTOR_LABELS["unsupported_claims"], "warn", 0.35,
                              f"{len(unsupported)} absolute or guaranteed claim(s) need support."))
        labels.append("unsupported claim")
    else:
        factors.append(Factor("unsupported_claims", FACTOR_LABELS["unsupported_claims"], "pass", 1.0,
                              "No absolute claims detected."))

    # 7. Risk routing ---------------------------------------------------------
    if risk_category == "URGENT" or escalation:
        factors.append(Factor("risk_routing", FACTOR_LABELS["risk_routing"], "fail", 0.0,
                              "Emergency language detected — routed to escalation guidance."))
        labels.append("escalation required")
    elif risk_category == "OUT_OF_SCOPE":
        factors.append(Factor("risk_routing", FACTOR_LABELS["risk_routing"], "warn", 0.5,
                              "Request is outside the assistant's scope; a limited answer was returned."))
        labels.append("out of scope")
    else:
        factors.append(Factor("risk_routing", FACTOR_LABELS["risk_routing"], "pass", 1.0,
                              "No escalation trigger detected."))

    score = sum(FACTOR_WEIGHTS[f.key] * f.score for f in factors) * 100
    if not labels:
        labels.append("sources found" if passages else "general information")
    return SafetyReport(score=round(score, 1), factors=factors, labels=labels)


def score_to_decimal(value: float) -> Decimal:
    return Decimal(str(round(value, 2)))
