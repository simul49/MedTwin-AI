"""Synthetic / manipulated-content analysis — EXPERIMENTAL (PRD §16).

No validated detector model is bundled with this release. The routine below
computes a small set of image forensics indicators and reports them as
probabilistic signals with an explicit uncertainty value. It never claims a file
is genuine or fake, and it is gated behind a feature flag in the UI.
"""
import logging
import math
from collections import Counter
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

DETECTOR_VERSION = "heuristic-indicators-0.1"

LIMITATIONS = (
    "Experimental capability. No validated detector model is configured: these are "
    "indicator heuristics, not evidence. False positives and false negatives are "
    "both possible. Verify any content through its original publisher, a trusted "
    "source, or a qualified professional."
)


def _shannon_entropy(counter: Counter, total: int) -> float:
    if not total:
        return 0.0
    return -sum((count / total) * math.log2(count / total) for count in counter.values() if count)


def analyse_image(path: Path) -> Dict:
    """Return indicators, a risk level and an uncertainty estimate."""
    from PIL import Image, ExifTags

    indicators: List[Dict] = []
    with Image.open(path) as image:
        width, height = image.size
        mode = image.mode
        exif = {}
        try:
            raw = image.getexif()
            exif = {ExifTags.TAGS.get(k, k): v for k, v in raw.items()} if raw else {}
        except Exception:  # pragma: no cover - defensive
            exif = {}

        grayscale = image.convert("L")
        pixels = list(grayscale.getdata())
        histogram = Counter(pixels)
        entropy = _shannon_entropy(histogram, len(pixels))

    indicators.append(
        {
            "key": "luminance_entropy",
            "label": "Luminance entropy",
            "value": round(entropy, 3),
            "interpretation": (
                "Very high or very low entropy can indicate synthetic smoothing or noise."
            ),
        }
    )
    indicators.append(
        {
            "key": "camera_metadata",
            "label": "Camera metadata",
            "value": "present" if exif else "absent",
            "interpretation": (
                "Absent capture metadata is common for AI-generated images, but also for "
                "screenshots and re-encoded files."
            ),
        }
    )
    indicators.append(
        {
            "key": "resolution",
            "label": "Resolution",
            "value": f"{width}x{height} ({mode})",
            "interpretation": "Unusual or very small resolutions reduce indicator reliability.",
        }
    )

    score = 0.0
    if not exif:
        score += 0.25
    if entropy > 7.6 or entropy < 4.2:
        score += 0.25
    if width < 512 or height < 512:
        score += 0.15

    if score >= 0.5:
        risk = "MEDIUM"
    elif score >= 0.3:
        risk = "LOW"
    else:
        risk = "LOW"

    return {
        "indicators": indicators,
        "riskLevel": risk,
        "signalStrength": round(min(1.0, score), 3),
        "uncertainty": 0.65,
        "limitations": LIMITATIONS,
        "detectorVersion": DETECTOR_VERSION,
    }
