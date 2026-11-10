"""Small in-memory rate limiter for sign-in (PRD §8.1).

Deliberately dependency-free and process-local: it protects against casual
brute-force attempts in a single-instance deployment. A multi-instance
deployment should replace this with a shared store (Redis) — the call sites
stay identical.
"""
import time
from collections import deque
from typing import Deque, Dict, Tuple

WINDOW_SECONDS = 15 * 60
MAX_ATTEMPTS = 8

_failures: Dict[str, Deque[float]] = {}


def _prune(bucket: Deque[float], now: float) -> None:
    while bucket and now - bucket[0] > WINDOW_SECONDS:
        bucket.popleft()


def key_for(email: str, ip: str = "") -> str:
    return f"{(email or '').strip().lower()}|{ip or ''}"


def check(key: str) -> Tuple[bool, int]:
    """Return ``(allowed, retry_after_seconds)``."""
    now = time.time()
    bucket = _failures.setdefault(key, deque())
    _prune(bucket, now)
    if len(bucket) >= MAX_ATTEMPTS:
        return False, max(1, int(WINDOW_SECONDS - (now - bucket[0])))
    return True, 0


def record_failure(key: str) -> None:
    _failures.setdefault(key, deque()).append(time.time())


def reset(key: str) -> None:
    _failures.pop(key, None)
