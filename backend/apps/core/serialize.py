"""Serialisation helpers shared by every API module."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional


def iso(value: Optional[Any]) -> Optional[str]:
    """ISO-8601 for datetimes/dates, tolerant of strings that already are."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def num(value: Optional[Any]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def money(value: Optional[Any]) -> Optional[str]:
    return None if value is None else str(value)


def camel(d: dict) -> dict:  # pragma: no cover - readability helper
    return d
