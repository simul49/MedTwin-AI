"""Digital Twin endpoints: records, observations, allergies, medications,
documents, timeline and the doctor's authorised view (PRD §9, §10, §19)."""
import logging
import os
import re
from pathlib import Path
from typing import List

from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import ROLE_DOCTOR, ROLE_PATIENT, User
from apps.accounts.serializers import serialize_user
from apps.consent.models import ConsentGrant
from apps.consent.serializers import serialize_grant
from apps.core.permissions import (
    ROLE_ADMIN,
    grant_scope,
    patient_queryset_for_doctor,
    require_roles,
    resolve_patient_for,
)
from apps.core.serialize import iso, num
from apps.core.utils import new_id, record_audit
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
from apps.twin.serializers import (
    serialize_allergy,
    serialize_document,
    serialize_extraction,
    serialize_medication,
    serialize_observation,
    serialize_record,
    serialize_timeline_event,
)

logger = logging.getLogger(__name__)

RECORD_CATEGORY_VALUES = {c[0] for c in HealthRecord._meta.get_field("category").choices}
SCOPE_CATEGORY_MAP = {
    "profile": [],
    "conditions": ["CONDITION", "FAMILY_HISTORY"],
    "medications": ["MEDICATION"],
    "allergies": ["ALLERGY"],
    "lab_results": ["LAB_RESULT", "VITAL"],
    "documents": [],
    "timeline": [],
}
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _serialize_profile(patient) -> dict:
    profile = getattr(patient, "patient_profile", None)
    if profile is None:
        return {}
    return {
        "dateOfBirth": iso(profile.date_of_birth),
        "age": profile.age,
        "gender": profile.gender,
        "bloodType": profile.blood_type or "",
        "heightCm": num(profile.height_cm),
        "weightKg": num(profile.weight_kg),
        "city": profile.city or "",
        "emergencyContact": profile.emergency_contact or "",
        "summary": profile.summary or "",
    }


def _allowed_categories(scope: List[str]) -> List[str]:
    if "all" in scope:
        return sorted(RECORD_CATEGORY_VALUES)
    categories: List[str] = []
    for key in scope or []:
        categories.extend(SCOPE_CATEGORY_MAP.get(key, []))
    return sorted(set(categories))


def _freshness(patient) -> dict:
    unverified = patient.health_records.filter(verification_status="UNVERIFIED").count()
    last = patient.health_records.order_by("-updated_at").first()
    missing = []
    if not patient.allergies.exists():
        missing.append("allergies")
    if not patient.medications.exists():
        missing.append("medications")
    if not patient.observations.exists():
        missing.append("observations")
    return {
        "lastUpdated": iso(getattr(last, "updated_at", None)),
        "unverifiedCount": unverified,
        "missingSections": missing,
    }


class DigitalTwinAPI(APIView):
    """Full Digital Twin for the signed-in patient (PRD §9.2)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        patient = request.user
        records = patient.health_records.all()[:50]
        consents = ConsentGrant.objects.filter(patient=patient).select_related("doctor").order_by("-created_at")
        return Response(
            {
                "patient": serialize_user(patient, detailed=True),
                "profile": _serialize_profile(patient),
                "counts": {
                    "records": patient.health_records.count(),
                    "observations": patient.observations.count(),
                    "allergies": patient.allergies.count(),
                    "medications": patient.medications.count(),
                    "documents": patient.documents.count(),
                    "timeline": patient.timeline_events.count(),
                },
                "records": [serialize_record(r) for r in records],
                "observations": [serialize_observation(o) for o in patient.observations.all()[:20]],
                "allergies": [serialize_allergy(a) for a in patient.allergies.all()[:20]],
                "medications": [serialize_medication(m) for m in patient.medications.all()[:20]],
                "timeline": [serialize_timeline_event(e) for e in patient.timeline_events.all()[:30]],
                "freshness": _freshness(patient),
                "consents": [serialize_grant(g) for g in consents],
            }
        )


class RecordListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        category = request.query_params.get("category") or ""
        query = (request.query_params.get("q") or "").strip()
        records = request.user.health_records.all()
        if category and category in RECORD_CATEGORY_VALUES:
            records = records.filter(category=category)
        if query:
            records = records.filter(title__icontains=query)
        return Response({"results": [serialize_record(r) for r in records[:100]]})

    @require_roles(ROLE_PATIENT, ROLE_DOCTOR)
    def post(self, request):
        data = request.data
        if request.user.role == ROLE_DOCTOR:
            patient = resolve_patient_for(request.user, data.get("patientId") or "")
        else:
            patient = request.user

        category = (data.get("category") or "NOTE").upper()
        if category not in RECORD_CATEGORY_VALUES:
            return Response({"error": "Unknown record category."}, status=status.HTTP_400_BAD_REQUEST)
        title = (data.get("title") or "").strip()
        if not title:
            return Response({"error": "A title is required."}, status=status.HTTP_400_BAD_REQUEST)

        authored_by_clinician = request.user.role == ROLE_DOCTOR
        record = HealthRecord.objects.create(
            id=new_id(),
            patient=patient,
            category=category,
            title=title,
            summary=(data.get("summary") or "").strip() or None,
            payload=data.get("payload") or None,
            source_type="CLINICIAN" if authored_by_clinician else "USER",
            verification_status="CLINICIAN_CONFIRMED" if authored_by_clinician else "USER_CONFIRMED",
            author=request.user,
            recorded_at=timezone.now(),
        )
        TimelineEvent.objects.create(
            id=new_id(),
            patient=patient,
            event_type="RECORD_ADDED",
            title=title,
            description=(data.get("summary") or "")[:500] or None,
            occurred_at=timezone.now(),
            source_type=record.source_type,
            source_id=record.id,
        )
        record_audit(action="RECORD_CREATE", request=request, actor=request.user,
                     resource_type="health_record", resource_id=record.id,
                     metadata={"category": category, "patientId": patient.id})
        return Response(serialize_record(record), status=status.HTTP_201_CREATED)


class RecordDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, record_id):
        try:
            record = HealthRecord.objects.get(pk=record_id)
        except HealthRecord.DoesNotExist:
            raise Http404
        if request.user.role == ROLE_PATIENT and record.patient_id != request.user.id:
            raise Http404
        if request.user.role == ROLE_DOCTOR and not grant_scope(request.user, record.patient):
            raise Http404
        return record

    def get(self, request, record_id):
        return Response(serialize_record(self._get(request, record_id)))

    def patch(self, request, record_id):
        record = self._get(request, record_id)
        data = request.data
        for field in ("title", "summary", "category"):
            if field in data and data[field] is not None:
                setattr(record, field, data[field])
        if "payload" in data:
            record.payload = data["payload"]
        if "verificationStatus" in data and data["verificationStatus"]:
            record.verification_status = data["verificationStatus"]
        record.save()
        record_audit(action="RECORD_UPDATE", request=request, actor=request.user,
                     resource_type="health_record", resource_id=record.id)
        return Response(serialize_record(record))

    def delete(self, request, record_id):
        record = self._get(request, record_id)
        if request.user.role == ROLE_DOCTOR:
            return Response({"error": "Doctors cannot delete patient records."},
                            status=status.HTTP_403_FORBIDDEN)
        record_audit(action="RECORD_DELETE", request=request, actor=request.user,
                     resource_type="health_record", resource_id=record.id)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TimelineAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        event_type = request.query_params.get("type") or ""
        events = request.user.timeline_events.all()
        if event_type:
            events = events.filter(event_type=event_type)
        return Response({"results": [serialize_timeline_event(e) for e in events[:100]]})


class ObservationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        return Response({"results": [serialize_observation(o) for o in request.user.observations.all()[:100]]})


class AllergyListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        return Response({"results": [serialize_allergy(a) for a in request.user.allergies.all()]})

    @require_roles(ROLE_PATIENT)
    def post(self, request):
        substance = (request.data.get("substance") or "").strip()
        if not substance:
            return Response({"error": "Name the substance."}, status=status.HTTP_400_BAD_REQUEST)
        allergy = Allergy.objects.create(
            id=new_id(),
            patient=request.user,
            substance=substance,
            reaction=(request.data.get("reaction") or "").strip() or None,
            severity=(request.data.get("severity") or "UNKNOWN").upper(),
            status=(request.data.get("status") or "ACTIVE").upper(),
            source_type="USER",
        )
        record_audit(action="ALLERGY_CREATE", request=request, actor=request.user,
                     resource_type="allergy", resource_id=allergy.id)
        return Response(serialize_allergy(allergy), status=status.HTTP_201_CREATED)


class AllergyDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, allergy_id):
        try:
            allergy = Allergy.objects.get(pk=allergy_id, patient=request.user)
        except Allergy.DoesNotExist:
            raise Http404
        return allergy

    def patch(self, request, allergy_id):
        allergy = self._get(request, allergy_id)
        data = request.data
        for field in ("substance", "reaction", "severity", "status"):
            if field in data and data[field] is not None:
                setattr(allergy, field, data[field])
        if data.get("reviewed"):
            allergy.reviewed_at = timezone.now()
        allergy.save()
        return Response(serialize_allergy(allergy))

    def delete(self, request, allergy_id):
        allergy = self._get(request, allergy_id)
        allergy.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MedicationListAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        return Response({"results": [serialize_medication(m) for m in request.user.medications.all()]})

    @require_roles(ROLE_PATIENT)
    def post(self, request):
        name = (request.data.get("name") or "").strip()
        if not name:
            return Response({"error": "Name the medication."}, status=status.HTTP_400_BAD_REQUEST)
        medication = Medication.objects.create(
            id=new_id(),
            patient=request.user,
            name=name,
            dose=(request.data.get("dose") or "").strip() or None,
            frequency=(request.data.get("frequency") or "").strip() or None,
            route=(request.data.get("route") or "").strip() or None,
            status=(request.data.get("status") or "ACTIVE").upper(),
            started_at=request.data.get("started_at") or None,
            source_type="USER",
        )
        record_audit(action="MEDICATION_CREATE", request=request, actor=request.user,
                     resource_type="medication", resource_id=medication.id)
        return Response(serialize_medication(medication), status=status.HTTP_201_CREATED)


class MedicationDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, medication_id):
        try:
            return Medication.objects.get(pk=medication_id, patient=request.user)
        except Medication.DoesNotExist:
            raise Http404

    def patch(self, request, medication_id):
        medication = self._get(request, medication_id)
        for field in ("name", "dose", "frequency", "route", "status", "started_at", "ended_at"):
            if field in request.data and request.data[field] is not None:
                setattr(medication, field, request.data[field])
        medication.save()
        return Response(serialize_medication(medication))

    def delete(self, request, medication_id):
        self._get(request, medication_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentListAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        return Response({"results": [serialize_document(d) for d in request.user.documents.all()]})

    @require_roles(ROLE_PATIENT)
    def post(self, request):
        upload = request.FILES.get("file")
        if upload is None:
            return Response({"error": "Choose a file to upload."}, status=status.HTTP_400_BAD_REQUEST)

        name = upload.name or "document"
        suffix = Path(name).suffix.lower()
        if suffix not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            return Response(
                {"error": f"Unsupported file type '{suffix}'. Allowed: PDF, PNG, JPG."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if upload.size > settings.MAX_UPLOAD_BYTES:
            return Response({"error": "File exceeds the 15 MB limit."},
                            status=status.HTTP_400_BAD_REQUEST)
        if (upload.content_type or "") not in settings.ALLOWED_UPLOAD_MIME:
            return Response({"error": "File contents do not match an allowed type."},
                            status=status.HTTP_400_BAD_REQUEST)

        patient = request.user
        safe = SAFE_NAME_RE.sub("_", Path(name).stem)[:60] or "document"
        relative = Path(patient.id) / f"{new_id()}_{safe}{suffix}"
        target = Path(settings.MEDIA_ROOT) / relative
        target.parent.mkdir(parents=True, exist_ok=True)

        with open(target, "wb+") as destination:
            for chunk in upload.chunks():
                destination.write(chunk)

        document = Document.objects.create(
            id=new_id(),
            owner=patient,
            patient=patient,
            name=name[:255],
            mime_type=upload.content_type or "application/octet-stream",
            size_bytes=upload.size,
            storage_path=str(relative),
            sha256=extraction.sha256_of(target),
            category=(request.data.get("category") or "OTHER").upper()[:40],
            processing_status="PROCESSING",
            uploaded_by=patient,
        )

        text, page_count, error = extraction.extract_text(target, document.mime_type)
        document.extracted_text = text or None
        document.page_count = page_count or None
        document.processing_status = "PROCESSED" if not error else "FAILED"
        document.processing_error = error or None
        document.processed_at = timezone.now()
        document.save()

        for field in extraction.derive_fields(text):
            DocumentExtraction.objects.create(id=new_id(), document=document, **field)

        TimelineEvent.objects.create(
            id=new_id(),
            patient=patient,
            event_type="DOCUMENT_UPLOADED",
            title=f"Uploaded {document.name}",
            description=(error or f"{len(text)} characters extracted.")[:500],
            occurred_at=timezone.now(),
            source_type="EXTRACTED",
            source_id=document.id,
        )
        record_audit(action="DOCUMENT_UPLOAD", request=request, actor=patient,
                     resource_type="document", resource_id=document.id,
                     metadata={"size": upload.size, "status": document.processing_status})

        return Response(
            serialize_document(document, extractions=document.extractions.all()),
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def _get(self, request, document_id):
        try:
            document = Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            raise Http404
        if request.user.role == ROLE_PATIENT and document.patient_id != request.user.id:
            raise Http404
        if request.user.role == ROLE_DOCTOR and not grant_scope(request.user, document.patient):
            raise Http404
        return document

    def get(self, request, document_id):
        document = self._get(request, document_id)
        return Response(serialize_document(document, extractions=document.extractions.all()))

    def delete(self, request, document_id):
        document = self._get(request, document_id)
        if request.user.role != ROLE_PATIENT:
            return Response({"error": "Only the patient can delete this document."},
                            status=status.HTTP_403_FORBIDDEN)
        path = Path(settings.MEDIA_ROOT) / document.storage_path
        if path.exists():
            os.remove(path)
        record_audit(action="DOCUMENT_DELETE", request=request, actor=request.user,
                     resource_type="document", resource_id=document.id)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentFileAPI(APIView):
    """Authorised download — files never live in a public directory."""

    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        try:
            document = Document.objects.get(pk=document_id)
        except Document.DoesNotExist:
            raise Http404
        if request.user.role == ROLE_PATIENT and document.patient_id != request.user.id:
            raise Http404
        if request.user.role == ROLE_DOCTOR:
            scope = grant_scope(request.user, document.patient)
            if "documents" not in scope and "all" not in scope:
                raise Http404

        path = Path(settings.MEDIA_ROOT) / document.storage_path
        if not path.exists():
            raise Http404
        record_audit(action="DOCUMENT_DOWNLOAD", request=request, actor=request.user,
                     resource_type="document", resource_id=document.id)
        return FileResponse(open(path, "rb"), as_attachment=True, filename=document.name)


class ExtractionReviewAPI(APIView):
    """Confirm, correct or reject an extracted field (PRD §10.2)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, document_id, extraction_id):
        try:
            document = Document.objects.get(pk=document_id, patient=request.user)
            item = DocumentExtraction.objects.get(pk=extraction_id, document=document)
        except (Document.DoesNotExist, DocumentExtraction.DoesNotExist):
            raise Http404

        review_status = (request.data.get("status") or "").upper()
        if review_status not in {"CONFIRMED", "CORRECTED", "REJECTED"}:
            return Response({"error": "Status must be CONFIRMED, CORRECTED or REJECTED."},
                            status=status.HTTP_400_BAD_REQUEST)
        if review_status == "CORRECTED":
            item.value = (request.data.get("value") or item.value or "")[:255]
        item.review_status = review_status
        item.save()
        record_audit(action="EXTRACTION_REVIEW", request=request, actor=request.user,
                     resource_type="document_extraction", resource_id=item.id,
                     metadata={"status": review_status})
        return Response(serialize_extraction(item))


class PatientExportAPI(APIView):
    """Data portability export (PRD §9.2)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def get(self, request):
        patient = request.user
        record_audit(action="DATA_EXPORT", request=request, actor=patient,
                     resource_type="patient", resource_id=patient.id)
        return Response(
            {
                "exportedAt": iso(timezone.now()),
                "patient": serialize_user(patient, detailed=True),
                "profile": _serialize_profile(patient),
                "records": [serialize_record(r) for r in patient.health_records.all()],
                "observations": [serialize_observation(o) for o in patient.observations.all()],
                "allergies": [serialize_allergy(a) for a in patient.allergies.all()],
                "medications": [serialize_medication(m) for m in patient.medications.all()],
                "documents": [serialize_document(d) for d in patient.documents.all()],
                "timeline": [serialize_timeline_event(e) for e in patient.timeline_events.all()],
            }
        )


class PatientDeleteDataAPI(APIView):
    """Erase the patient's health data (PRD §9.2, §23.2)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_PATIENT)
    def delete(self, request):
        patient = request.user
        for document in patient.documents.all():
            path = Path(settings.MEDIA_ROOT) / document.storage_path
            if path.exists():
                os.remove(path)
        patient.health_records.all().delete()
        patient.observations.all().delete()
        patient.allergies.all().delete()
        patient.medications.all().delete()
        patient.timeline_events.all().delete()
        patient.documents.all().delete()
        record_audit(action="DATA_DELETE", request=request, actor=patient,
                     resource_type="patient", resource_id=patient.id)
        return Response({"ok": True})


# ---------------------------------------------------------------------------
# Doctor views — only patients with an effective grant are reachable
# ---------------------------------------------------------------------------
class AuthorizedPatientsAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR)
    def get(self, request):
        patients = patient_queryset_for_doctor(request.user)
        results = []
        for patient in patients:
            grant = ConsentGrant.objects.filter(
                doctor=request.user, patient=patient, status="ACTIVE"
            ).order_by("-created_at").first()
            profile = getattr(patient, "patient_profile", None)
            results.append(
                {
                    "id": patient.id,
                    "name": patient.name,
                    "email": patient.email,
                    "initials": patient.initials,
                    "avatarColor": patient.avatar_color,
                    "age": profile.age if profile else None,
                    "gender": profile.gender if profile else "UNDISCLOSED",
                    "scope": grant.scope if grant else [],
                    "expiresAt": iso(grant.expires_at) if grant else None,
                    "openFlags": patient.observations.exclude(flag__in=["NORMAL", "UNKNOWN"]).count(),
                    "recordCount": patient.health_records.count(),
                    "lastActivity": iso(
                        getattr(patient.timeline_events.order_by("-occurred_at").first(), "occurred_at", None)
                    ),
                }
            )
        return Response({"results": results})


class DoctorPatientSummaryAPI(APIView):
    """Source-linked summary draft for an authorised patient (PRD §19.2)."""

    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR)
    def get(self, request, patient_id):
        patient = resolve_patient_for(request.user, patient_id)
        scope = grant_scope(request.user, patient)
        categories = _allowed_categories(scope)

        records = patient.health_records.filter(category__in=categories)[:50] if categories else []
        payload = {
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "email": patient.email,
                "initials": patient.initials,
            },
            "scope": scope,
            "profile": _serialize_profile(patient) if "profile" in scope or "all" in scope else {},
            "records": [serialize_record(r) for r in records],
            "observations": (
                [serialize_observation(o) for o in patient.observations.all()[:20]]
                if "lab_results" in scope or "all" in scope
                else []
            ),
            "allergies": (
                [serialize_allergy(a) for a in patient.allergies.all()]
                if "allergies" in scope or "all" in scope
                else []
            ),
            "medications": (
                [serialize_medication(m) for m in patient.medications.all()]
                if "medications" in scope or "all" in scope
                else []
            ),
            "documents": (
                [serialize_document(d) for d in patient.documents.all()]
                if "documents" in scope or "all" in scope
                else []
            ),
            "timeline": (
                [serialize_timeline_event(e) for e in patient.timeline_events.all()[:30]]
                if "timeline" in scope or "all" in scope
                else []
            ),
        }

        existing = (
            patient.health_records.filter(source_type="AI_GENERATED", category="NOTE")
            .order_by("-created_at")
            .first()
        )
        payload["draftSummary"] = serialize_record(existing) if existing else None

        record_audit(action="PATIENT_VIEW", request=request, actor=request.user,
                     resource_type="patient", resource_id=patient.id,
                     metadata={"scope": scope})
        return Response(payload)

    @require_roles(ROLE_DOCTOR)
    def post(self, request, patient_id):
        """Create an AI-draft summary. Always stored as an unverified draft."""
        patient = resolve_patient_for(request.user, patient_id)
        scope = grant_scope(request.user, patient)
        categories = _allowed_categories(scope)
        records = list(patient.health_records.filter(category__in=categories)[:20]) if categories else []
        meds = list(patient.medications.filter(status="ACTIVE")[:10]) if ("medications" in scope or "all" in scope) else []
        allergies = list(patient.allergies.all()[:10]) if ("allergies" in scope or "all" in scope) else []
        observations = list(patient.observations.order_by("-observed_at")[:10]) if ("lab_results" in scope or "all" in scope) else []

        lines = ["AI-generated draft summary — NOT clinician-verified.", ""]
        lines.append(f"Patient: {patient.name}")
        if records:
            lines.append("")
            lines.append("Conditions and history:")
            lines.extend(f"- {r.title} ({r.verification_status.lower().replace('_', ' ')})" for r in records)
        if meds:
            lines.append("")
            lines.append("Active medications:")
            lines.extend(f"- {m.name} {m.dose or ''} {m.frequency or ''}".strip() for m in meds)
        if allergies:
            lines.append("")
            lines.append("Allergies:")
            lines.extend(f"- {a.substance} ({a.severity.lower()})" for a in allergies)
        if observations:
            lines.append("")
            lines.append("Recent results:")
            lines.extend(f"- {o.label}: {o.display_value} ({o.flag.lower()})" for o in observations)
        lines.append("")
        lines.append("Sources: patient Digital Twin records only. Requires clinician review before use.")

        # Keep exactly one unreviewed AI draft per patient: regenerating updates
        # the existing draft instead of piling up near-identical records.
        summary = "\n".join(lines)[:4000]
        record = (
            patient.health_records.filter(
                source_type="AI_GENERATED", verification_status="UNVERIFIED"
            )
            .order_by("-created_at")
            .first()
        )
        created = record is None
        if record is None:
            record = HealthRecord(
                id=new_id(),
                patient=patient,
                category="NOTE",
                title="AI draft summary (requires review)",
                source_type="AI_GENERATED",
                verification_status="UNVERIFIED",
                author=request.user,
            )
        record.summary = summary
        record.recorded_at = timezone.now()
        record.save()

        record_audit(action="SUMMARY_DRAFT_CREATE" if created else "SUMMARY_DRAFT_UPDATE",
                     request=request, actor=request.user,
                     resource_type="health_record", resource_id=record.id,
                     metadata={"patientId": patient.id})
        return Response(serialize_record(record), status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class DoctorPatientRecordsAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR)
    def get(self, request, patient_id):
        patient = resolve_patient_for(request.user, patient_id)
        categories = _allowed_categories(grant_scope(request.user, patient))
        records = patient.health_records.all()
        if categories:
            records = records.filter(category__in=categories)
        return Response({"results": [serialize_record(r) for r in records[:100]]})


class DoctorPatientDocumentsAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR)
    def get(self, request, patient_id):
        patient = resolve_patient_for(request.user, patient_id)
        scope = grant_scope(request.user, patient)
        if "documents" not in scope and "all" not in scope:
            return Response({"results": []})
        return Response({"results": [serialize_document(d) for d in patient.documents.all()]})


class DoctorPatientTimelineAPI(APIView):
    permission_classes = [IsAuthenticated]

    @require_roles(ROLE_DOCTOR)
    def get(self, request, patient_id):
        patient = resolve_patient_for(request.user, patient_id)
        scope = grant_scope(request.user, patient)
        if "timeline" not in scope and "all" not in scope:
            return Response({"results": []})
        return Response({"results": [serialize_timeline_event(e) for e in patient.timeline_events.all()[:100]]})
