"""Reminder/notification system for upcoming secret expirations and rotation due dates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from envault.ttl import get_ttl, list_expiring
from envault.rotation import get_rotation_metadata, is_rotation_due


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def expiring_soon(secrets: dict[str, Any], within_seconds: int = 86400) -> list[dict]:
    """Return secrets whose TTL will expire within *within_seconds* seconds."""
    results = []
    for key in list(secrets.keys()):
        if key.startswith("__"):
            continue
        expiry = get_ttl(secrets, key)
        if expiry is None:
            continue
        delta = (expiry - _now()).total_seconds()
        if 0 < delta <= within_seconds:
            results.append({"key": key, "expires_at": expiry.isoformat(), "seconds_remaining": int(delta)})
    return results


def rotation_overdue(secrets: dict[str, Any]) -> list[dict]:
    """Return secrets for which rotation is currently due."""
    results = []
    for key in list(secrets.keys()):
        if key.startswith("__"):
            continue
        if is_rotation_due(secrets, key):
            meta = get_rotation_metadata(secrets, key)
            last = meta.get("last_rotated", "never")
            results.append({"key": key, "last_rotated": last})
    return results


def reminder_report(secrets: dict[str, Any], within_seconds: int = 86400) -> dict:
    """Build a combined reminder report."""
    return {
        "expiring_soon": expiring_soon(secrets, within_seconds),
        "rotation_overdue": rotation_overdue(secrets),
    }
