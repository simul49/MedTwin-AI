"""Educational recommendation engine (PRD §17).

Recommendations are educational only: they never prescribe, never change a
medication, and always state the basis they were derived from so the user can
dismiss or correct them (PRD §17.2).
"""
from typing import Dict, List

from apps.ai.models import Recommendation
from apps.core.utils import new_id

EDUCATION_TOPICS = {
    "Hypertension": {
        "title": "Understanding blood-pressure readings",
        "body": (
            "Learn what systolic and diastolic numbers mean, how home readings differ "
            "from clinic readings, and which measurement habit gives the most useful trend."
        ),
    },
    "Type 2 diabetes": {
        "title": "What HbA1c tells you — and what it does not",
        "body": (
            "HbA1c reflects average blood glucose over roughly three months. It does not "
            "show day-to-day swings, so home readings still matter."
        ),
    },
    "Asthma": {
        "title": "Recognising your asthma triggers",
        "body": (
            "Keeping a short symptom diary helps your clinician separate well-controlled "
            "periods from patterns that need a plan change."
        ),
    },
    "Hyperlipidaemia": {
        "title": "Reading a lipid panel",
        "body": (
            "LDL, HDL and triglycerides answer different questions. Ask your clinician "
            "which number is the target for you personally."
        ),
    },
    "Anaemia": {
        "title": "Why haemoglobin matters",
        "body": (
            "Haemoglobin carries oxygen through your body. Low levels often show up as "
            "tiredness or shortness of breath — worth tracking alongside your iron panel."
        ),
    },
    "Hypothyroidism": {
        "title": "Understanding thyroid results",
        "body": (
            "TSH, T3 and T4 tell different parts of the thyroid story. Bring all three to "
            "your review so trends can be compared over time."
        ),
    },
    "Chronic kidney disease": {
        "title": "Protecting kidney health",
        "body": (
            "Creatinine and eGFR estimates track how well kidneys filter. Staying hydrated "
            "and reviewing blood-pressure control both help."
        ),
    },
    "Obesity": {
        "title": "Small steps for sustainable change",
        "body": (
            "Modest, consistent changes — regular meal timing, daily movement and sleep — "
            "usually beat short intensive efforts for long-term results."
        ),
    },
    "Anxiety": {
        "title": "Managing anxious moments",
        "body": (
            "Breathing exercises, regular sleep and noting triggers are evidence-informed "
            "first steps. Your clinician can suggest structured options if needed."
        ),
    },
}


def _ensure(user, *, type: str, title: str, body: str, basis: Dict) -> Recommendation:
    existing = Recommendation.objects.filter(user=user, title=title, status="ACTIVE").first()
    if existing:
        return existing
    return Recommendation.objects.create(
        id=new_id(),
        user=user,
        type=type,
        title=title,
        body=body,
        basis=basis,
        status="ACTIVE",
    )


def refresh_for_patient(user) -> List[Recommendation]:
    """Rebuild the ACTIVE recommendation set from the patient's twin."""
    created: List[Recommendation] = []

    for condition in user.health_records.filter(category="CONDITION")[:5]:
        topic = EDUCATION_TOPICS.get(condition.title)
        if topic:
            created.append(
                _ensure(
                    user,
                    type="EDUCATION",
                    title=topic["title"],
                    body=topic["body"],
                    basis={"condition": condition.title, "recordId": condition.id},
                )
            )

    flagged = user.observations.exclude(flag__in=["NORMAL", "UNKNOWN"]).order_by("-observed_at")[:5]
    for observation in flagged:
        created.append(
            _ensure(
                user,
                type="QUESTION_TO_ASK",
                title=f"Ask your clinician about {observation.label}",
                body=(
                    f"Your most recent {observation.label} was flagged "
                    f"{observation.flag.lower()}. Ask what follow-up interval is right for you."
                ),
                basis={"observationId": observation.id, "flag": observation.flag},
            )
        )
        created.append(
            _ensure(
                user,
                type="QUESTION_TO_ASK",
                title=f"What target should you aim for with {observation.label}?",
                body=(
                    f"Your latest {observation.label} is flagged {observation.flag.lower()}. Ask "
                    "your clinician which target range suits you, what follow-up test to expect, "
                    "and which lifestyle steps would move it in the right direction."
                ),
                basis={"observationId": observation.id, "flag": observation.flag},
            )
        )

    created.append(
        _ensure(
            user,
            type="LIFESTYLE",
            title="Build a home-measurement habit",
            body=(
                "Measure at the same time of day, seated and rested. Consistent conditions "
                "make every trend in your Digital Twin far more meaningful."
            ),
            basis={},
        )
    )
    created.append(
        _ensure(
            user,
            type="LIFESTYLE",
            title="Add a short daily walk",
            body=(
                "Ten to twenty minutes of walking most days supports blood pressure, glucose "
                "control and sleep quality. Start small and keep it regular."
            ),
            basis={},
        )
    )
    created.append(
        _ensure(
            user,
            type="LIFESTYLE",
            title="Keep a steady sleep window",
            body=(
                "Going to bed and waking at similar times helps blood pressure, appetite and "
                "mood regulation. Aim for a consistent window rather than total hours alone."
            ),
            basis={},
        )
    )

    active_meds = user.medications.filter(status="ACTIVE")[:5]
    if active_meds:
        created.append(
            _ensure(
                user,
                type="FOLLOW_UP",
                title="Keep your medication list current",
                body=(
                    f"You have {len(active_meds)} medication(s) marked active. Confirm the dose "
                    "and frequency are still correct at your next review."
                ),
                basis={"medicationCount": len(active_meds)},
            )
        )

    unverified = user.health_records.filter(verification_status="UNVERIFIED")[:5]
    if unverified:
        created.append(
            _ensure(
                user,
                type="NEXT_STEP",
                title="Confirm extracted record details",
                body=(
                    f"{len(unverified)} record(s) still need your confirmation. Reviewing them "
                    "keeps your Digital Twin trustworthy for every future answer."
                ),
                basis={"unverifiedCount": len(unverified)},
            )
        )

    return [r for r in created if r is not None]
