"""TTL (time-to-live) enforcement for vault secrets."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

_TTL_META_KEY = "__ttl__"


def _get_ttl_index(secrets: Dict[str, str]) -> Dict[str, float]:
    """Return the TTL index stored inside the secrets dict."""
    import json

    raw = secrets.get(_TTL_META_KEY, "{}")
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _set_ttl_index(secrets: Dict[str, str], index: Dict[str, float]) -> None:
    """Persist the TTL index back into the secrets dict."""
    import json

    secrets[_TTL_META_KEY] = json.dumps(index)


def set_ttl(secrets: Dict[str, str], key: str, ttl_seconds: float) -> None:
    """Record an expiry timestamp for *key* (now + ttl_seconds).

    Raises KeyError if *key* does not exist in *secrets*.
    Raises ValueError if *key* is the reserved TTL meta-key.
    """
    if key == _TTL_META_KEY:
        raise ValueError(f"Key '{key}' is reserved for internal TTL metadata.")
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in secrets.")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be a positive number.")

    index = _get_ttl_index(secrets)
    index[key] = time.time() + ttl_seconds
    _set_ttl_index(secrets, index)


def get_ttl(secrets: Dict[str, str], key: str) -> Optional[float]:
    """Return the expiry epoch for *key*, or None if no TTL is set."""
    return _get_ttl_index(secrets).get(key)


def is_expired(secrets: Dict[str, str], key: str) -> bool:
    """Return True if *key* has a TTL that has already elapsed."""
    expiry = get_ttl(secrets, key)
    if expiry is None:
        return False
    return time.time() >= expiry


def remove_ttl(secrets: Dict[str, str], key: str) -> None:
    """Remove the TTL entry for *key* (no-op if none exists)."""
    index = _get_ttl_index(secrets)
    index.pop(key, None)
    _set_ttl_index(secrets, index)


def list_expired(secrets: Dict[str, str]) -> List[str]:
    """Return a list of keys whose TTL has elapsed."""
    now = time.time()
    index = _get_ttl_index(secrets)
    return [k for k, exp in index.items() if now >= exp]
