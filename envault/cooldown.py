"""Cooldown: prevent a secret from being modified too soon after its last change."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

COOLDOWN_KEY = "__cooldowns__"


class CooldownActiveError(Exception):
    """Raised when a secret is still within its cooldown period."""

    def __init__(self, key: str, remaining_seconds: float) -> None:
        self.key = key
        self.remaining_seconds = remaining_seconds
        super().__init__(
            f"Secret '{key}' is in cooldown for another {remaining_seconds:.0f}s."
        )


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_cooldown_index(secrets: dict) -> dict:
    import json

    raw = secrets.get(COOLDOWN_KEY, "{}")
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _set_cooldown_index(secrets: dict, index: dict) -> None:
    import json

    secrets[COOLDOWN_KEY] = json.dumps(index)


def set_cooldown(secrets: dict, key: str, seconds: int) -> None:
    """Record that *key* was just modified and must not be changed for *seconds*."""
    if key not in secrets or key.startswith("__"):
        raise KeyError(f"Key '{key}' not found or is internal.")
    if seconds <= 0:
        raise ValueError("Cooldown seconds must be a positive integer.")
    index = _get_cooldown_index(secrets)
    index[key] = {
        "locked_at": _now().isoformat(),
        "duration": seconds,
    }
    _set_cooldown_index(secrets, index)


def get_cooldown(secrets: dict, key: str) -> Optional[dict]:
    """Return cooldown metadata for *key*, or None if none is set."""
    return _get_cooldown_index(secrets).get(key)


def remove_cooldown(secrets: dict, key: str) -> None:
    """Remove any cooldown entry for *key*."""
    index = _get_cooldown_index(secrets)
    index.pop(key, None)
    _set_cooldown_index(secrets, index)


def is_in_cooldown(secrets: dict, key: str) -> bool:
    """Return True if *key* is currently within its cooldown window."""
    entry = get_cooldown(secrets, key)
    if entry is None:
        return False
    locked_at = datetime.fromisoformat(entry["locked_at"])
    elapsed = (_now() - locked_at).total_seconds()
    return elapsed < entry["duration"]


def assert_not_in_cooldown(secrets: dict, key: str) -> None:
    """Raise CooldownActiveError if *key* is in cooldown."""
    entry = get_cooldown(secrets, key)
    if entry is None:
        return
    locked_at = datetime.fromisoformat(entry["locked_at"])
    elapsed = (_now() - locked_at).total_seconds()
    remaining = entry["duration"] - elapsed
    if remaining > 0:
        raise CooldownActiveError(key, remaining)


def list_cooled_keys(secrets: dict) -> list[str]:
    """Return all keys that are currently in an active cooldown window."""
    return [k for k in _get_cooldown_index(secrets) if is_in_cooldown(secrets, k)]
