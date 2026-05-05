"""Secret value history — track previous values for each key."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

MAX_HISTORY = 20
_HISTORY_KEY = "__history__"


def _get_history_index(secrets: dict) -> dict:
    raw = secrets.get(_HISTORY_KEY)
    if isinstance(raw, dict):
        return raw
    return {}


def _set_history_index(secrets: dict, index: dict) -> None:
    secrets[_HISTORY_KEY] = index


def record_history(secrets: dict, key: str, old_value: str) -> None:
    """Append *old_value* to the history for *key* before it is overwritten."""
    if key.startswith("__"):
        return
    index = _get_history_index(secrets)
    entries: list[dict[str, Any]] = index.get(key, [])
    entries.append(
        {
            "value": old_value,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    # Keep only the most recent MAX_HISTORY entries
    index[key] = entries[-MAX_HISTORY:]
    _set_history_index(secrets, index)


def get_history(secrets: dict, key: str) -> list[dict[str, Any]]:
    """Return the history list for *key* (oldest first)."""
    if key not in secrets and not key.startswith("__"):
        raise KeyError(f"Key '{key}' not found in vault.")
    return list(_get_history_index(secrets).get(key, []))


def clear_history(secrets: dict, key: str) -> None:
    """Remove all history entries for *key*."""
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in vault.")
    index = _get_history_index(secrets)
    index.pop(key, None)
    _set_history_index(secrets, index)


def list_keys_with_history(secrets: dict) -> list[str]:
    """Return all keys that have at least one history entry."""
    return [k for k, v in _get_history_index(secrets).items() if v]
