"""Secret lifecycle management: track creation, activation, deprecation, and retirement."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

VALID_STATES = ("active", "deprecated", "retired")
_LIFECYCLE_KEY = "__lifecycle__"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_lifecycle_index(secrets: dict) -> dict:
    import json
    raw = secrets.get(_LIFECYCLE_KEY, "{}")
    return json.loads(raw) if isinstance(raw, str) else raw


def _set_lifecycle_index(secrets: dict, index: dict) -> None:
    import json
    secrets[_LIFECYCLE_KEY] = json.dumps(index)


def set_state(secrets: dict, key: str, state: str, reason: str = "") -> None:
    """Set the lifecycle state of a secret key."""
    if key.startswith("__"):
        raise KeyError(f"Cannot manage lifecycle of internal key: {key}")
    if key not in secrets:
        raise KeyError(f"Key not found: {key}")
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state '{state}'. Must be one of: {VALID_STATES}")
    index = _get_lifecycle_index(secrets)
    entry = index.get(key, {})
    entry["state"] = state
    entry["updated_at"] = _now()
    if reason:
        entry["reason"] = reason
    if "created_at" not in entry:
        entry["created_at"] = _now()
    index[key] = entry
    _set_lifecycle_index(secrets, index)


def get_state(secrets: dict, key: str) -> Optional[Dict]:
    """Return lifecycle metadata for a key, or None if not set."""
    index = _get_lifecycle_index(secrets)
    return index.get(key)


def list_by_state(secrets: dict, state: str) -> List[str]:
    """Return all keys currently in the given lifecycle state."""
    if state not in VALID_STATES:
        raise ValueError(f"Invalid state '{state}'. Must be one of: {VALID_STATES}")
    index = _get_lifecycle_index(secrets)
    return [k for k, v in index.items() if v.get("state") == state]


def remove_state(secrets: dict, key: str) -> None:
    """Remove lifecycle metadata for a key."""
    index = _get_lifecycle_index(secrets)
    if key not in index:
        raise KeyError(f"No lifecycle metadata for key: {key}")
    del index[key]
    _set_lifecycle_index(secrets, index)
