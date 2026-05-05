"""Watch secrets for changes and trigger hooks or notifications."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Callable, Dict, Optional

_WATCH_STATE_KEY = "__watch_state__"


def _secret_fingerprint(secrets: dict) -> Dict[str, str]:
    """Return a dict mapping each non-internal key to an MD5 of its value."""
    return {
        k: hashlib.md5(str(v).encode()).hexdigest()
        for k, v in secrets.items()
        if not k.startswith("__")
    }


def get_watch_state(secrets: dict) -> Dict[str, str]:
    """Load the previously saved fingerprint state from the vault."""
    raw = secrets.get(_WATCH_STATE_KEY, "{}")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def save_watch_state(secrets: dict, state: Dict[str, str]) -> None:
    """Persist the current fingerprint state into the secrets dict (in-place)."""
    secrets[_WATCH_STATE_KEY] = json.dumps(state)


def detect_changes(
    secrets: dict,
) -> Dict[str, str]:
    """
    Compare current secrets against the saved watch state.

    Returns a dict of {key: change_type} where change_type is one of:
    'added', 'removed', 'modified'.
    """
    previous = get_watch_state(secrets)
    current = _secret_fingerprint(secrets)
    changes: Dict[str, str] = {}

    for key, digest in current.items():
        if key not in previous:
            changes[key] = "added"
        elif previous[key] != digest:
            changes[key] = "modified"

    for key in previous:
        if key not in current:
            changes[key] = "removed"

    return changes


def watch_secrets(
    secrets: dict,
    callback: Callable[[str, str], None],
    interval: float = 2.0,
    iterations: Optional[int] = None,
) -> None:
    """
    Poll for secret changes and invoke callback(key, change_type) on each change.

    Args:
        secrets:    The mutable secrets dict (updated externally between polls).
        callback:   Called with (key, change_type) for every detected change.
        interval:   Seconds between polls.
        iterations: If set, stop after this many poll cycles (useful for testing).
    """
    count = 0
    while iterations is None or count < iterations:
        changes = detect_changes(secrets)
        for key, change_type in changes.items():
            callback(key, change_type)
        if changes:
            save_watch_state(secrets, _secret_fingerprint(secrets))
        count += 1
        if iterations is None or count < iterations:
            time.sleep(interval)
