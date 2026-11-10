from apps.core.serialize import iso, num


def serialize_record(record) -> dict:
    return {
        "id": record.id,
        "category": record.category,
        "title": record.title,
        "summary": record.summary or "",
        "payload": record.payload or {},
        "sourceType": record.source_type,
        "verificationStatus": record.verification_status,
        "sourceDocumentId": record.source_document_id,
        "authorId": record.author_id,
        "recordedAt": iso(record.recorded_at),
        "createdAt": iso(record.created_at),
        "updatedAt": iso(record.updated_at),
        "isAiGenerated": record.is_ai_generated,
    }


def serialize_observation(observation) -> dict:
    raw = num(observation.value_numeric)
    # Trim DECIMAL artefacts (7.1000 -> 7.1, 132.0000 -> 132).
    value = int(raw) if raw is not None and float(raw).is_integer() else raw
    return {
        "id": observation.id,
        "code": observation.code or "",
        "label": observation.label,
        "value": value,
        "valueText": observation.value_text or "",
        "displayValue": observation.display_value,
        "unit": observation.unit or "",
        "referenceRange": observation.reference_range or "",
        "flag": observation.flag,
        "observedAt": iso(observation.observed_at),
        "sourceType": observation.source_type,
    }


def serialize_allergy(allergy) -> dict:
    return {
        "id": allergy.id,
        "substance": allergy.substance,
        "reaction": allergy.reaction or "",
        "severity": allergy.severity,
        "status": allergy.status,
        "sourceType": allergy.source_type,
        "reviewedAt": iso(allergy.reviewed_at),
        "createdAt": iso(allergy.created_at),
    }


def serialize_medication(medication) -> dict:
    return {
        "id": medication.id,
        "name": medication.name,
        "dose": medication.dose or "",
        "frequency": medication.frequency or "",
        "route": medication.route or "",
        "status": medication.status,
        "startedAt": iso(medication.started_at),
        "endedAt": iso(medication.ended_at),
        "sourceType": medication.source_type,
    }


def serialize_extraction(extraction) -> dict:
    return {
        "id": extraction.id,
        "fieldName": extraction.field_name,
        "label": extraction.label or "",
        "value": extraction.value or "",
        "confidence": num(extraction.confidence),
        "reviewStatus": extraction.review_status,
        "evidence": extraction.evidence or "",
    }


def serialize_document(document, *, extractions=None) -> dict:
    payload = {
        "id": document.id,
        "name": document.name,
        "mimeType": document.mime_type,
        "sizeBytes": document.size_bytes,
        "category": document.category,
        "processingStatus": document.processing_status,
        "processingError": document.processing_error or "",
        "pageCount": document.page_count,
        "createdAt": iso(document.created_at),
        "processedAt": iso(document.processed_at),
        "hasExtractedText": bool(document.extracted_text),
    }
    if extractions is not None:
        payload["extractions"] = [serialize_extraction(e) for e in extractions]
    return payload


def serialize_timeline_event(event) -> dict:
    return {
        "id": event.id,
        "eventType": event.event_type,
        "title": event.title,
        "description": event.description or "",
        "occurredAt": iso(event.occurred_at),
        "sourceType": event.source_type,
        "sourceId": event.source_id,
    }
