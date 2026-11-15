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
    "Image uploaded successfully, but OCR is unavailable on the server — no text "
    "could be extracted. Upload a PDF with a text layer instead."
)

OCR_MAX_PAGES = 8


def _ocr_pdf(path: Path, max_pages: int = OCR_MAX_PAGES) -> Tuple[str, int]:
    """Render scanned PDF pages to images and OCR them."""
    import io

    import fitz  # PyMuPDF
    import pytesseract
    from PIL import Image

    doc = fitz.open(str(path))
    page_count = len(doc)
    pages = []
    for index in range(min(page_count, max_pages)):
        pix = doc[index].get_pixmap(dpi=200)
        image = Image.open(io.BytesIO(pix.tobytes("png")))
        pages.append(pytesseract.image_to_string(image) or "")
    doc.close()
    return "\n".join(pages).strip(), page_count


def _ocr_image(path: Path) -> str:
    import pytesseract
    from PIL import Image

    return pytesseract.image_to_string(Image.open(str(path))).strip()


def _ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401

        return True
    except ImportError:
        return False


def extract_text_full(path: Path, mime_type: str) -> Tuple[str, int, str, str]:
    """Return ``(text, page_count, error, method)`` with method in
    ``text-layer`` | ``ocr`` | ``none``."""
    try:
        if mime_type == "application/pdf":
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages = []
            for page in reader.pages[:40]:
                pages.append(page.extract_text() or "")
            text = "\n".join(pages).strip()
            if text:
                return text, len(reader.pages), "", "text-layer"
            # No text layer — likely a scan: fall back to OCR.
            if _ocr_available():
                text, _ = _ocr_pdf(path)
                if text:
                    return text, len(reader.pages), "", "ocr"
                return "", len(reader.pages), "No readable text found even via OCR — the scan may be blank or very low quality.", "none"
            return "", len(reader.pages), "No text layer found in this PDF (likely a scan).", "none"

        if mime_type in {"image/png", "image/jpeg"}:
            if _ocr_available():
                text = _ocr_image(path)
                if text:
                    return text, 1, "", "ocr"
                return "", 1, "No readable text found in this image via OCR.", "none"
            return "", 1, NOTE_NO_OCR, "none"

        return "", 0, f"Unsupported type for extraction: {mime_type}", "none"
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("extraction failed for %s: %s", path, exc)
        return "", 0, f"Extraction failed: {exc}", "none"


def extract_text(path: Path, mime_type: str) -> Tuple[str, int, str]:
    """Backwards-compatible wrapper returning ``(text, page_count, error)``."""
    text, page_count, error, _method = extract_text_full(path, mime_type)
    return text, page_count, error


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
