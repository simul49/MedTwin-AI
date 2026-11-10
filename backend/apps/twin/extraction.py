"""Document text extraction and candidate field detection (PRD §10).

Extraction output is a *candidate*: every field is stored with a confidence
value and ``PENDING`` review status, and nothing becomes verified until a human
confirms it (PRD §10.2 step 6-7, §9.3).
"""
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

FIELD_PATTERNS = [
    ("hba1c", "HbA1c", r"(?:hba1c|hgba1c|a1c)\D{0,12}(\d{1,2}(?:[.,]\d)?)\s*%?", 0.72),
    ("glucose", "Glucose", r"\b(?:glucose|blood sugar)\D{0,12}(\d{2,3}(?:[.,]\d)?)\b", 0.66),
    ("cholesterol_total", "Total cholesterol", r"\b(?:total cholesterol|cholesterol)\D{0,12}(\d{2,3}(?:[.,]\d)?)\b", 0.62),
    ("ldl", "LDL", r"\bldl\D{0,12}(\d{2,3}(?:[.,]\d)?)\b", 0.68),
    ("hdl", "HDL", r"\bhdl\D{0,12}(\d{2,3}(?:[.,]\d)?)\b", 0.68),
    ("blood_pressure", "Blood pressure", r"\b(?:bp|blood pressure)\D{0,10}(\d{2,3})\s*/\s*(\d{2,3})", 0.75),
    ("heart_rate", "Heart rate", r"\b(?:heart rate|pulse|hr)\D{0,10}(\d{2,3})\s*(?:bpm)?", 0.6),
    ("weight", "Weight", r"\bweight\D{0,10}(\d{2,3}(?:[.,]\d)?)\s*kg", 0.6),
    ("height", "Height", r"\bheight\D{0,10}(\d{2,3}(?:[.,]\d)?)\s*cm", 0.6),
    ("document_date", "Document date", r"\b(\d{4}-\d{2}-\d{2})\b", 0.7),
]

NOTE_NO_OCR = (
    "Image uploaded successfully. No OCR engine is configured, so no text was "
    "extracted — review the file manually or upload a PDF with a text layer."
)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_text(path: Path, mime_type: str) -> Tuple[str, int, str]:
    """Return ``(text, page_count, error)``."""
    try:
        if mime_type == "application/pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages[:40]:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages).strip()
            if not text:
                return "", len(reader.pages), "No text layer found in this PDF (likely a scan)."
            return text, len(reader.pages), ""

        if mime_type in {"image/png", "image/jpeg"}:
            return "", 1, NOTE_NO_OCR

        return "", 0, f"Unsupported type for extraction: {mime_type}"
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("extraction failed for %s: %s", path, exc)
        return "", 0, f"Extraction failed: {exc}"


def derive_fields(text: str) -> List[Dict]:
    """Find candidate structured values inside extracted text."""
    if not text:
        return []

    found: List[Dict] = []
    for field_name, label, pattern, confidence in FIELD_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        groups = [g for g in match.groups() if g]
        value = "/".join(groups) if field_name == "blood_pressure" else groups[0]
        start = max(0, match.start() - 30)
        found.append(
            {
                "field_name": field_name,
                "label": label,
                "value": value.replace(",", "."),
                "confidence": confidence,
                "evidence": text[start : match.end() + 30].replace("\n", " ")[:400],
            }
        )
    return found
