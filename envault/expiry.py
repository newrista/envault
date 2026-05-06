"""Secret expiry management: set, check, and list expiring secrets."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

_EXPIRY_KEY = "__expiry_index__"
_DATE_FMT = "%Y-%m-%dT%H:%M:%S"


class SecretAlreadyExpiredError(ValueError):
    """Raised when trying to set expiry on an already-expired secret."""


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _get_expiry_index(secrets: dict) -> dict:
    import json
    raw = secrets.get(_EXPIRY_KEY, "{}")
    return json.loads(raw)


def _set_expiry_index(secrets: dict, index: dict) -> None:
    import json
    secrets[_EXPIRY_KEY] = json.dumps(index)


def set_expiry(secrets: dict, key: str, days: int) -> datetime:
    """Set an expiry date `days` from now for `key`."""
    if key not in secrets or key.startswith("__"):
        raise KeyError(f"Key not found: {key!r}")
    if days <= 0:
        raise ValueError("days must be a positive integer")
    index = _get_expiry_index(secrets)
    expiry = _now() + timedelta(days=days)
    index[key] = expiry.strftime(_DATE_FMT)
    _set_expiry_index(secrets, index)
    return expiry


def get_expiry(secrets: dict, key: str) -> Optional[datetime]:
    """Return the expiry datetime for `key`, or None if not set."""
    index = _get_expiry_index(secrets)
    raw = index.get(key)
    if raw is None:
        return None
    return datetime.strptime(raw, _DATE_FMT).replace(tzinfo=timezone.utc)


def remove_expiry(secrets: dict, key: str) -> bool:
    """Remove expiry for `key`. Returns True if an entry was removed."""
    index = _get_expiry_index(secrets)
    if key not in index:
        return False
    del index[key]
    _set_expiry_index(secrets, index)
    return True


def is_expired(secrets: dict, key: str) -> bool:
    """Return True if the secret has passed its expiry date."""
    expiry = get_expiry(secrets, key)
    if expiry is None:
        return False
    return _now() >= expiry


def list_expiring(secrets: dict, within_days: int = 7) -> list[tuple[str, datetime]]:
    """Return keys expiring within `within_days` days, sorted by expiry."""
    cutoff = _now() + timedelta(days=within_days)
    index = _get_expiry_index(secrets)
    result = []
    for key, raw in index.items():
        expiry = datetime.strptime(raw, _DATE_FMT).replace(tzinfo=timezone.utc)
        if expiry <= cutoff:
            result.append((key, expiry))
    result.sort(key=lambda t: t[1])
    return result
