"""Archive (soft-delete) secrets without permanently removing them."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

ARCHIVED_KEY = "__archived__"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_archive_index(secrets: dict) -> Dict[str, dict]:
    raw = secrets.get(ARCHIVED_KEY)
    if isinstance(raw, dict):
        return raw
    return {}


def _set_archive_index(secrets: dict, index: Dict[str, dict]) -> None:
    secrets[ARCHIVED_KEY] = index


def archive_secret(secrets: dict, key: str, reason: str = "") -> None:
    """Soft-delete a secret by moving it to the archive index."""
    if key.startswith("__"):
        raise KeyError(f"Cannot archive internal key: {key}")
    if key not in secrets:
        raise KeyError(f"Key not found: {key}")
    index = _get_archive_index(secrets)
    index[key] = {
        "value": secrets.pop(key),
        "archived_at": _now(),
        "reason": reason,
    }
    _set_archive_index(secrets, index)


def restore_secret(secrets: dict, key: str) -> None:
    """Restore a previously archived secret back into the active vault."""
    index = _get_archive_index(secrets)
    if key not in index:
        raise KeyError(f"Archived key not found: {key}")
    entry = index.pop(key)
    secrets[key] = entry["value"]
    _set_archive_index(secrets, index)


def get_archived(secrets: dict, key: str) -> Optional[dict]:
    """Return archive metadata for a key, or None if not archived."""
    return _get_archive_index(secrets).get(key)


def list_archived(secrets: dict) -> List[str]:
    """Return a list of all archived secret keys."""
    return list(_get_archive_index(secrets).keys())


def purge_archived(secrets: dict, key: str) -> None:
    """Permanently delete an archived secret (cannot be undone)."""
    index = _get_archive_index(secrets)
    if key not in index:
        raise KeyError(f"Archived key not found: {key}")
    del index[key]
    _set_archive_index(secrets, index)
