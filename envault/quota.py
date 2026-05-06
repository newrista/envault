"""Quota management: enforce per-vault limits on secret count and value size."""

from __future__ import annotations

DEFAULT_MAX_SECRETS = 500
DEFAULT_MAX_VALUE_BYTES = 4096

_QUOTA_KEY = "__quota__"


class QuotaExceededError(Exception):
    """Raised when a quota limit would be exceeded."""


def _get_quota(secrets: dict) -> dict:
    import json
    raw = secrets.get(_QUOTA_KEY)
    if raw is None:
        return {}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _set_quota(secrets: dict, quota: dict) -> None:
    import json
    secrets[_QUOTA_KEY] = json.dumps(quota)


def set_quota(secrets: dict, max_secrets: int | None = None, max_value_bytes: int | None = None) -> None:
    """Persist quota settings into the secrets dict."""
    quota = _get_quota(secrets)
    if max_secrets is not None:
        if max_secrets < 1:
            raise ValueError("max_secrets must be >= 1")
        quota["max_secrets"] = max_secrets
    if max_value_bytes is not None:
        if max_value_bytes < 1:
            raise ValueError("max_value_bytes must be >= 1")
        quota["max_value_bytes"] = max_value_bytes
    _set_quota(secrets, quota)


def get_quota(secrets: dict) -> dict:
    """Return effective quota settings (with defaults filled in)."""
    quota = _get_quota(secrets)
    return {
        "max_secrets": quota.get("max_secrets", DEFAULT_MAX_SECRETS),
        "max_value_bytes": quota.get("max_value_bytes", DEFAULT_MAX_VALUE_BYTES),
    }


def check_quota(secrets: dict, new_key: str, new_value: str) -> None:
    """Raise QuotaExceededError if adding/updating new_key=new_value would breach limits."""
    quota = get_quota(secrets)
    user_keys = [k for k in secrets if not k.startswith("__")]
    is_new = new_key not in user_keys
    projected_count = len(user_keys) + (1 if is_new else 0)
    if projected_count > quota["max_secrets"]:
        raise QuotaExceededError(
            f"Secret count would exceed limit of {quota['max_secrets']} (currently {len(user_keys)})"
        )
    value_bytes = len(new_value.encode())
    if value_bytes > quota["max_value_bytes"]:
        raise QuotaExceededError(
            f"Value size {value_bytes}B exceeds limit of {quota['max_value_bytes']}B for key '{new_key}'"
        )


def quota_status(secrets: dict) -> dict:
    """Return a status snapshot: limits and current usage."""
    quota = get_quota(secrets)
    user_keys = [k for k in secrets if not k.startswith("__")]
    return {
        "max_secrets": quota["max_secrets"],
        "max_value_bytes": quota["max_value_bytes"],
        "used_secrets": len(user_keys),
        "remaining_secrets": max(0, quota["max_secrets"] - len(user_keys)),
    }
