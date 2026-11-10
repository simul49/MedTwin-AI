"""Seed the database with synthetic demo data.

Everything created here is fictional (PRD §23.2: use synthetic data during
development and demos). Idempotent: re-running only adds what is missing.

    .venv/bin/python manage.py seed_demo
    .venv/bin/python manage.py seed_demo --reset     # wipe demo data first
"""
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import DoctorProfile, PatientProfile, Role, User
from apps.ai.models import KnowledgeChunk, KnowledgeSource
from apps.consent.models import ConsentGrant
from apps.connect.models import Appointment, Conversation, Message, Notification
from apps.core.utils import new_id
from apps.ops.models import AuditLog, FeatureFlag, ModelVersion
from apps.twin import extraction
from apps.twin.models import (
    Allergy,
    Document,
    DocumentExtraction,
    HealthRecord,
    Medication,
    Observation,
    TimelineEvent,
)

PASSWORD = "MedTwin@2026"


def _pdf_bytes(lines) -> bytes:
    """Build a minimal single-page PDF so the extraction pipeline has input."""
    text_ops = ["BT", "/F1 12 Tf", "72 780 Td", "16 TL"]
    for line in lines:
        escaped = line.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")
        text_ops.append(f"({escaped}) Tj T*")
    text_ops.append("ET")
    content = "\n".join(text_ops).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{index} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n"
    ).encode()
    return bytes(out)


class Command(BaseCommand):
    help = "Seed synthetic demo data (users, twin records, knowledge base, consents)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo data before seeding.")

    def handle(self, *args, **options):
        if options["reset"]:
            self._reset()
        self._roles()
        users = self._users()
        self._twin(users)
        self._documents(users)
        self._consents(users)
        self._conversations(users)
        self._appointments(users)
        self._knowledge()
        self._flags()
        self._models()
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write("  patient@medtwin.dev / MedTwin@2026")
        self.stdout.write("  doctor@medtwin.dev  / MedTwin@2026")
        self.stdout.write("  admin@medtwin.dev   / MedTwin@2026")

    # -- helpers ------------------------------------------------------------
    def _reset(self):
        AuditLog.objects.all().delete()
        ConsentGrant.objects.all().delete()
        Message.objects.all().delete()
        Conversation.objects.all().delete()
        Appointment.objects.all().delete()
        Notification.objects.all().delete()
        DocumentExtraction.objects.all().delete()
        Document.objects.all().delete()
        Observation.objects.all().delete()
        Medication.objects.all().delete()
        Allergy.objects.all().delete()
        HealthRecord.objects.all().delete()
        TimelineEvent.objects.all().delete()
        KnowledgeChunk.objects.all().delete()
        KnowledgeSource.objects.all().delete()
        User.objects.exclude(role="ADMIN").delete()
        self.stdout.write("Existing demo data cleared.")

    def _roles(self):
        for code, name in [
            ("PATIENT", "Patient"),
            ("DOCTOR", "Healthcare professional"),
            ("ADMIN", "Administrator"),
            ("RESEARCHER", "Research operator"),
        ]:
            Role.objects.get_or_create(code=code, defaults={"id": new_id(), "name": name})

    def _user(self, email, name, role):
        user = User.objects.filter(email=email).first()
        if user:
            return user
        user = User.objects.create(
            id=new_id(),
            name=name,
            email=email,
            role=role,
            avatar_color="#2563eb",
            is_active=True,
            is_verified=True,
            language="en",
        )
        user.set_password(PASSWORD)
        user.save(update_fields=["password"])
        return user

    def _users(self):
        priya = self._user("patient@medtwin.dev", "Priya Raman", "PATIENT")
        PatientProfile.objects.get_or_create(
            user=priya,
            defaults={
                "id": new_id(),
                "date_of_birth": date(1987, 4, 12),
                "gender": "FEMALE",
                "blood_type": "O+",
                "height_cm": 164,
                "weight_kg": 61.5,
                "city": "Singapore",
                "emergency_contact": "R. Raman (+65 9000 1111)",
                "summary": "Manages type 2 diabetes and hypertension; reviews results quarterly.",
            },
        )

        marc = self._user("marc@medtwin.dev", "Marc Oyelaran", "PATIENT")
        PatientProfile.objects.get_or_create(
            user=marc,
            defaults={
                "id": new_id(),
                "date_of_birth": date(1975, 9, 30),
                "gender": "MALE",
                "blood_type": "A-",
                "height_cm": 179,
                "weight_kg": 88,
                "city": "Lagos",
                "summary": "Hyperlipidaemia under review; no current medication.",
            },
        )

        chen = self._user("doctor@medtwin.dev", "Dr. Lian Chen", "DOCTOR")
        DoctorProfile.objects.get_or_create(
            user=chen,
            defaults={
                "id": new_id(),
                "specialization": "Endocrinology",
                "license_number": "MCR-88213",
                "hospital": "Harbour General Hospital",
                "department": "Metabolic Medicine",
                "bio": "Focuses on diabetes management and patient education.",
                "verification_status": "VERIFIED",
                "verified_at": timezone.now(),
            },
        )

        amara = self._user("amara@medtwin.dev", "Dr. Amara Nwosu", "DOCTOR")
        DoctorProfile.objects.get_or_create(
            user=amara,
            defaults={
                "id": new_id(),
                "specialization": "Cardiology",
                "license_number": "MCR-77340",
                "hospital": "Lakeside Medical Centre",
                "department": "Preventive Cardiology",
                "bio": "Preventive cardiology and lipid management.",
                "verification_status": "VERIFIED",
                "verified_at": timezone.now(),
            },
        )

        self._user("admin@medtwin.dev", "Ada Whitfield", "ADMIN")
        return {"priya": priya, "marc": marc, "chen": chen, "amara": amara}

    def _twin(self, users):
        priya, marc = users["priya"], users["marc"]
        chen = users["chen"]

        if not priya.health_records.exists():
            rows = [
                ("CONDITION", "Type 2 diabetes", "Diagnosed 2019; reviewed every three months.", "CLINICIAN_CONFIRMED", "CLINICIAN"),
                ("CONDITION", "Hypertension", "Stage 1; managed with lifestyle and medication.", "CLINICIAN_CONFIRMED", "CLINICIAN"),
                ("FAMILY_HISTORY", "Mother — type 2 diabetes", "Diagnosed at age 58.", "USER_CONFIRMED", "USER"),
                ("PROCEDURE", "Retinal screening", "Annual eye screening, no retinopathy.", "CLINICIAN_CONFIRMED", "CLINICIAN"),
                ("IMMUNIZATION", "Influenza vaccine", "Annual vaccination.", "USER_CONFIRMED", "USER"),
                ("LAB_RESULT", "HbA1c 7.1%", "Most recent HbA1c from the quarterly panel.", "EXTRACTED_REVIEWED", "EXTRACTED"),
                ("NOTE", "Clinician note — medication review", "Continue current dose; recheck HbA1c in three months.", "CLINICIAN_CONFIRMED", "CLINICIAN"),
            ]
            for index, (category, title, summary, status, source) in enumerate(rows):
                HealthRecord.objects.create(
                    id=new_id(),
                    patient=priya,
                    category=category,
                    title=title,
                    summary=summary,
                    source_type=source,
                    verification_status=status,
                    author=chen if source == "CLINICIAN" else priya,
                    recorded_at=timezone.now() - timedelta(days=30 * (index + 1)),
                )

            for label, value, unit, flag, days, ref in [
                ("HbA1c", 7.1, "%", "HIGH", 18, "4.0 - 5.6"),
                ("Fasting glucose", 6.9, "mmol/L", "HIGH", 18, "3.9 - 5.5"),
                ("Systolic BP", 132, "mmHg", "HIGH", 12, "90 - 120"),
                ("Diastolic BP", 84, "mmHg", "NORMAL", 12, "60 - 80"),
                ("LDL cholesterol", 3.4, "mmol/L", "HIGH", 40, "0.0 - 3.0"),
                ("HDL cholesterol", 1.2, "mmol/L", "NORMAL", 40, "1.0 - 2.2"),
            ]:
                Observation.objects.create(
                    id=new_id(),
                    patient=priya,
                    label=label,
                    value_numeric=value,
                    unit=unit,
                    flag=flag,
                    reference_range=ref,
                    observed_at=timezone.now() - timedelta(days=days),
                    source_type="CLINICIAN",
                )

            Allergy.objects.create(
                id=new_id(), patient=priya, substance="Penicillin",
                reaction="Rash and swelling", severity="MODERATE", status="ACTIVE",
                source_type="USER", reviewed_at=timezone.now() - timedelta(days=120),
            )
            for name, dose, frequency in [
                ("Metformin", "500 mg", "Twice daily with meals"),
                ("Amlodipine", "5 mg", "Once daily"),
            ]:
                Medication.objects.create(
                    id=new_id(), patient=priya, name=name, dose=dose,
                    frequency=frequency, route="Oral", status="ACTIVE",
                    started_at=date.today() - timedelta(days=400), source_type="CLINICIAN",
                )

            for title, event_type, days, description in [
                ("HbA1c result uploaded", "LAB_RESULT", 18, "Quarterly panel processed."),
                ("Medication review", "APPOINTMENT", 30, "Dose confirmed; no change."),
                ("Blood pressure logged", "OBSERVATION", 12, "Home reading 132/84."),
                ("Annual eye screening", "PROCEDURE", 150, "No retinopathy detected."),
            ]:
                TimelineEvent.objects.create(
                    id=new_id(), patient=priya, event_type=event_type, title=title,
                    description=description, occurred_at=timezone.now() - timedelta(days=days),
                    source_type="CLINICIAN",
                )

        if not marc.health_records.exists():
            HealthRecord.objects.create(
                id=new_id(), patient=marc, category="CONDITION",
                title="Hyperlipidaemia", summary="Borderline high LDL; diet review planned.",
                source_type="USER", verification_status="USER_CONFIRMED",
                recorded_at=timezone.now() - timedelta(days=60),
            )
            Observation.objects.create(
                id=new_id(), patient=marc, label="Total cholesterol",
                value_numeric=5.9, unit="mmol/L", flag="HIGH",
                reference_range="0.0 - 5.2", observed_at=timezone.now() - timedelta(days=25),
                source_type="USER",
            )
            TimelineEvent.objects.create(
                id=new_id(), patient=marc, event_type="LAB_RESULT",
                title="Lipid panel uploaded", description="Total cholesterol 5.9 mmol/L.",
                occurred_at=timezone.now() - timedelta(days=25), source_type="USER",
            )

    def _documents(self, users):
        priya = users["priya"]
        if priya.documents.exists():
            return

        lines = [
            "Harbour General Hospital - Metabolic Medicine",
            "Laboratory report",
            f"Report date: {(timezone.now() - timedelta(days=18)).date().isoformat()}",
            "Patient: Priya Raman",
            "",
            "HbA1c: 7.1 %",
            "Glucose: 6.9 mmol/L",
            "Blood pressure: 132/84",
            "Total cholesterol: 5.2 mmol/L",
            "LDL: 3.4 mmol/L",
            "HDL: 1.2 mmol/L",
            "Heart rate: 74 bpm",
            "Weight: 61.5 kg",
            "",
            "Comment: continue current therapy; repeat panel in three months.",
        ]
        relative = Path(priya.id) / f"{new_id()}_lab_report.pdf"
        target = Path(settings.MEDIA_ROOT) / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_pdf_bytes(lines))

        document = Document.objects.create(
            id=new_id(),
            owner=priya,
            patient=priya,
            name="Quarterly lab report.pdf",
            mime_type="application/pdf",
            size_bytes=target.stat().st_size,
            storage_path=str(relative),
            sha256=extraction.sha256_of(target),
            category="LAB",
            processing_status="PROCESSING",
            uploaded_by=priya,
        )
        text, pages, error = extraction.extract_text(target, document.mime_type)
        document.extracted_text = text or None
        document.page_count = pages or None
        document.processing_status = "PROCESSED" if not error else "FAILED"
        document.processing_error = error or None
        document.processed_at = timezone.now()
        document.save()

        for field in extraction.derive_fields(text):
            DocumentExtraction.objects.create(id=new_id(), document=document, **field)

        TimelineEvent.objects.create(
            id=new_id(), patient=priya, event_type="DOCUMENT_UPLOADED",
            title="Uploaded Quarterly lab report.pdf",
            description="Text extracted; fields awaiting confirmation.",
            occurred_at=timezone.now() - timedelta(days=18), source_type="EXTRACTED",
            source_id=document.id,
        )

    def _consents(self, users):
        priya, marc, chen, amara = users["priya"], users["marc"], users["chen"], users["amara"]
        ConsentGrant.objects.get_or_create(
            patient=priya, doctor=chen, status="ACTIVE",
            defaults={
                "id": new_id(),
                "scope": ["profile", "conditions", "medications", "allergies", "lab_results", "documents", "timeline"],
                "purpose": "Quarterly diabetes review",
                "granted_at": timezone.now() - timedelta(days=45),
                "expires_at": timezone.now() + timedelta(days=45),
            },
        )
        ConsentGrant.objects.get_or_create(
            patient=marc, doctor=amara, status="PENDING",
            defaults={
                "id": new_id(),
                "scope": ["profile", "lab_results"],
                "purpose": "Lipid management second opinion",
                "expires_at": timezone.now() + timedelta(days=30),
            },
        )
        Notification.objects.get_or_create(
            user=marc, type="CONSENT_REQUEST",
            defaults={
                "id": new_id(),
                "title": "A doctor has requested access",
                "body": "Dr. Amara Nwosu requested access to your profile and lab results.",
                "link": "/consent",
            },
        )

    def _conversations(self, users):
        priya, chen = users["priya"], users["chen"]
        if Conversation.objects.filter(patient=priya, doctor=chen).exists():
            return
        conversation = Conversation.objects.create(
            id=new_id(), patient=priya, doctor=chen, channel="PATIENT_DOCTOR",
            title="Dr. Lian Chen",
        )
        for role, body, minutes in [
            ("USER", "Hello Dr. Chen — my latest HbA1c was 7.1%. Should I be concerned?", 600),
            ("DOCTOR", "Thanks for sharing. Let's review the full panel together at your next visit; keep logging your home readings.", 540),
            ("USER", "Understood, I'll bring my log.", 500),
        ]:
            Message.objects.create(
                id=new_id(), conversation=conversation,
                sender=priya if role == "USER" else chen, role=role, body=body,
                created_at=timezone.now() - timedelta(minutes=minutes),
                read_at=timezone.now() - timedelta(minutes=minutes - 5),
            )

    def _appointments(self, users):
        priya, chen = users["priya"], users["chen"]
        if Appointment.objects.filter(patient=priya).exists():
            return
        Appointment.objects.create(
            id=new_id(), patient=priya, doctor=chen,
            scheduled_at=timezone.now() + timedelta(days=12),
            duration_min=30, reason="Quarterly diabetes review", status="CONFIRMED",
        )
        Appointment.objects.create(
            id=new_id(), patient=priya, doctor=chen,
            scheduled_at=timezone.now() - timedelta(days=30),
            duration_min=30, reason="Medication review", status="COMPLETED",
        )

    def _knowledge(self):
        if KnowledgeSource.objects.exists():
            return
        sources = [
            {
                "title": "Understanding HbA1c",
                "publisher": "MedTwin AI Knowledge Office",
                "version": "2026.1",
                "url": "https://example.org/knowledge/hba1c",
                "category": "diabetes",
                "chunks": [
                    "HbA1c estimates average blood glucose over roughly the past two to three months. "
                    "It is reported as a percentage. Many guidelines describe below 5.7% as non-diabetic "
                    "range, 5.7% to 6.4% as intermediate, and 6.5% or above on two occasions as consistent "
                    "with diabetes, but the exact thresholds and their interpretation vary between "
                    "laboratories and countries.",
                    "HbA1c does not show day-to-day glucose swings. Two people with the same HbA1c can have "
                    "very different daily patterns, which is why home glucose readings or continuous "
                    "monitoring still add information that a single HbA1c cannot provide.",
                    "Conditions affecting red blood cells, pregnancy, and some haemoglobin variants can make "
                    "an HbA1c result misleading. When a result does not match the clinical picture, "
                    "clinicians may use a different test.",
                ],
            },
            {
                "title": "Reading a lipid panel",
                "publisher": "MedTwin AI Knowledge Office",
                "version": "2026.1",
                "url": "https://example.org/knowledge/lipids",
                "category": "cardiovascular",
                "chunks": [
                    "A standard lipid panel reports total cholesterol, LDL cholesterol, HDL cholesterol and "
                    "triglycerides. LDL and HDL answer different questions: higher LDL is generally "
                    "associated with greater cardiovascular risk, while HDL is involved in transporting "
                    "cholesterol back to the liver.",
                    "Reference ranges on a report are population ranges, not personal targets. The target "
                    "that matters for an individual depends on their overall risk, so the number to aim for "
                    "should be discussed with a clinician who knows the full history.",
                    "A single measurement is noisy. Lipid panels are usually interpreted as a trend, and "
                    "clinicians often repeat a test before making decisions about long-term therapy.",
                ],
            },
            {
                "title": "Home blood-pressure measurement",
                "publisher": "MedTwin AI Knowledge Office",
                "version": "2026.1",
                "url": "https://example.org/knowledge/blood-pressure",
                "category": "cardiovascular",
                "chunks": [
                    "Blood pressure is reported as two numbers: systolic pressure while the heart contracts "
                    "and diastolic pressure while it relaxes, measured in millimetres of mercury (mmHg).",
                    "A single reading is not a diagnosis. Blood pressure changes through the day and rises "
                    "with stress, exercise and recent caffeine, so a pattern of readings taken at rest is "
                    "far more informative than one measurement.",
                    "For a home reading, sit with your back supported and feet flat for five minutes, keep "
                    "the cuff at heart height, avoid talking, and take two readings one minute apart. "
                    "Record both, with the time of day.",
                ],
            },
            {
                "title": "When to seek urgent care",
                "publisher": "MedTwin AI Knowledge Office",
                "version": "2026.1",
                "url": "https://example.org/knowledge/urgent-care",
                "category": "safety",
                "chunks": [
                    "Chest pain, difficulty breathing, sudden weakness or numbness on one side, sudden "
                    "confusion, severe bleeding, loss of consciousness, or thoughts of harming yourself are "
                    "situations that require emergency services immediately rather than a digital tool.",
                    "A health application cannot examine you, run tests, or coordinate emergency response. "
                    "If a symptom is severe, sudden, or worsening, contact your local emergency number or a "
                    "clinician without waiting for an app to respond.",
                ],
            },
            {
                "title": "Preparing for a medical appointment",
                "publisher": "MedTwin AI Knowledge Office",
                "version": "2026.1",
                "url": "https://example.org/knowledge/appointments",
                "category": "self-management",
                "chunks": [
                    "Bring a current list of every medication and supplement you take, including the dose "
                    "and how often you take it. This is one of the most useful things you can give a "
                    "clinician and is a common source of missing information.",
                    "Write down your top two or three questions before the visit and ask them first. Short, "
                    "specific questions tend to get more useful answers than general ones.",
                    "Ask what the next step is and when it should happen. Knowing whether to book a follow-up, "
                    "repeat a test, or simply continue is often the most valuable outcome of a consultation.",
                ],
            },
        ]

        for spec in sources:
            source = KnowledgeSource.objects.create(
                id=new_id(),
                title=spec["title"],
                publisher=spec["publisher"],
                version=spec["version"],
                source_url=spec["url"],
                category=spec["category"],
                license_status="OPEN",
                review_status="APPROVED",
                ingested_at=timezone.now(),
            )
            for index, text in enumerate(spec["chunks"]):
                KnowledgeChunk.objects.create(
                    id=new_id(),
                    source=source,
                    chunk_index=index,
                    title=spec["title"],
                    text=text,
                    tokens=len(text.split()),
                    access_classification="PUBLIC",
                )

    def _flags(self):
        flags = [
            ("public_website", "Public website", "Informational site with the five required sections.", True, "RELEASED"),
            ("auth_rbac", "Authentication and RBAC", "Sign-up, sign-in, roles and least-privilege checks.", True, "RELEASED"),
            ("digital_twin", "Patient Digital Twin", "Structured records, timeline and provenance.", True, "IMPLEMENTED"),
            ("document_upload", "Document upload and extraction", "PDF/PNG/JPEG upload with reviewable extraction.", True, "IMPLEMENTED"),
            ("ai_assistant", "AI Healthcare Assistant", "Grounded answers with sources and limitations.", True, "IMPLEMENTED"),
            ("consent_workflow", "Consent and access grants", "Grant, review and revoke professional access.", True, "IMPLEMENTED"),
            ("recommendations", "Educational recommendations", "Context-aware educational suggestions.", True, "IN_DEVELOPMENT"),
            ("trust_safety", "AI Trust & Safety indicator", "Interpretable evaluation factors on every answer.", True, "IMPLEMENTED"),
            ("messaging", "Messaging and appointments", "Patient–doctor messaging and appointment requests.", True, "IMPLEMENTED"),
            ("content_analysis", "Synthetic-content analysis", "EXPERIMENTAL indicator heuristics.", False, "IN_DEVELOPMENT"),
            ("realtime_ws", "Real-time WebSocket updates", "Live updates for messaging and notifications.", False, "PLANNED"),
            ("video_consult", "Video consultation", "WebRTC or approved provider integration.", False, "PLANNED"),
        ]
        for key, label, description, enabled, status in flags:
            FeatureFlag.objects.get_or_create(
                flag_key=key,
                defaults={
                    "id": new_id(),
                    "label": label,
                    "description": description,
                    "is_enabled": enabled,
                    "status": status,
                },
            )

    def _models(self):
        ModelVersion.objects.get_or_create(
            name="MedTwin offline composer",
            version="1.0",
            defaults={
                "id": new_id(),
                "provider": "built-in",
                "kind": "LLM",
                "is_active": True,
                "config": {"mode": "extractive", "requiresKey": False},
            },
        )
        ModelVersion.objects.get_or_create(
            name="Trust & Safety evaluator",
            version="trust-v1.0",
            defaults={
                "id": new_id(),
                "provider": "built-in",
                "kind": "SAFETY",
                "is_active": True,
                "config": {"factors": 7},
            },
        )
        ModelVersion.objects.get_or_create(
            name="Content indicator heuristics",
            version="heuristic-indicators-0.1",
            defaults={
                "id": new_id(),
                "provider": "built-in",
                "kind": "DETECTOR",
                "is_active": False,
                "config": {"experimental": True},
            },
        )
