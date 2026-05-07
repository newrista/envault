"""Watermark support: embed and verify a tamper-evident fingerprint in a vault."""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any

_WATERMARK_KEY = "__watermark__"


def _is_internal(key: str) -> bool:
    return key.startswith("__") and key.endswith("__")


def _compute_fingerprint(secrets: dict[str, Any], label: str, ts: float) -> str:
    """Compute a SHA-256 fingerprint over the non-internal secrets."""
    payload = {
        k: v
        for k, v in sorted(secrets.items())
        if not _is_internal(k)
    }
    raw = json.dumps(payload, sort_keys=True) + label + str(ts)
    return hashlib.sha256(raw.encode()).hexdigest()


def stamp(secrets: dict[str, Any], label: str = "") -> dict[str, Any]:
    """Embed a watermark into *secrets* (mutates and returns the dict)."""
    ts = time.time()
    fingerprint = _compute_fingerprint(secrets, label, ts)
    secrets[_WATERMARK_KEY] = {
        "label": label,
        "timestamp": ts,
        "fingerprint": fingerprint,
    }
    return secrets


def verify(secrets: dict[str, Any]) -> "WatermarkResult":
    """Verify the watermark embedded in *secrets*."""
    entry = secrets.get(_WATERMARK_KEY)
    if not entry:
        return WatermarkResult(present=False, valid=False, label="", timestamp=None, fingerprint=None)

    label = entry.get("label", "")
    ts = entry.get("timestamp")
    stored = entry.get("fingerprint", "")
    expected = _compute_fingerprint(secrets, label, ts)
    return WatermarkResult(
        present=True,
        valid=stored == expected,
        label=label,
        timestamp=ts,
        fingerprint=stored,
    )


def remove(secrets: dict[str, Any]) -> dict[str, Any]:
    """Remove the watermark from *secrets* (mutates and returns the dict)."""
    secrets.pop(_WATERMARK_KEY, None)
    return secrets


class WatermarkResult:
    def __init__(
        self,
        present: bool,
        valid: bool,
        label: str,
        timestamp: float | None,
        fingerprint: str | None,
    ) -> None:
        self.present = present
        self.valid = valid
        self.label = label
        self.timestamp = timestamp
        self.fingerprint = fingerprint

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"WatermarkResult(present={self.present}, valid={self.valid}, "
            f"label={self.label!r})"
        )
