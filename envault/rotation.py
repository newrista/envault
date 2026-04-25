"""Secret rotation utilities for envault vaults."""

from datetime import datetime, timedelta
from typing import Optional

ROTATION_METADATA_KEY = "__rotation_meta__"


def get_rotation_metadata(secrets: dict) -> dict:
    """Extract rotation metadata from secrets dict."""
    return secrets.get(ROTATION_METADATA_KEY, {})


def set_rotation_metadata(secrets: dict, key: str, rotated_at: Optional[datetime] = None) -> dict:
    """Record rotation timestamp for a given secret key."""
    if rotated_at is None:
        rotated_at = datetime.utcnow()

    meta = get_rotation_metadata(secrets)
    meta[key] = rotated_at.isoformat()
    secrets[ROTATION_METADATA_KEY] = meta
    return secrets


def is_rotation_due(secrets: dict, key: str, max_age_days: int = 90) -> bool:
    """Return True if the secret has not been rotated within max_age_days."""
    meta = get_rotation_metadata(secrets)
    if key not in meta:
        return True

    rotated_at = datetime.fromisoformat(meta[key])
    age = datetime.utcnow() - rotated_at
    return age > timedelta(days=max_age_days)


def rotate_secret(secrets: dict, key: str, new_value: str) -> dict:
    """Replace a secret value and update its rotation timestamp."""
    if key == ROTATION_METADATA_KEY:
        raise ValueError(f"Cannot rotate reserved metadata key: {ROTATION_METADATA_KEY}")

    secrets[key] = new_value
    secrets = set_rotation_metadata(secrets, key)
    return secrets


def list_stale_secrets(secrets: dict, max_age_days: int = 90) -> list:
    """Return list of secret keys that are due for rotation."""
    stale = []
    for key in secrets:
        if key == ROTATION_METADATA_KEY:
            continue
        if is_rotation_due(secrets, key, max_age_days):
            stale.append(key)
    return stale
