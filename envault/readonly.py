"""Read-only mode for vault secrets — prevent accidental writes to protected keys."""

from __future__ import annotations

from typing import Dict, List

_READONLY_KEY = "__readonly__"


class ReadOnlyViolationError(Exception):
    """Raised when attempting to modify a read-only secret."""


def _get_readonly_index(secrets: dict) -> Dict[str, bool]:
    """Return the read-only index stored inside the secrets dict."""
    return dict(secrets.get(_READONLY_KEY, {}))


def _set_readonly_index(secrets: dict, index: Dict[str, bool]) -> None:
    """Persist the read-only index back into the secrets dict."""
    secrets[_READONLY_KEY] = index


def protect(secrets: dict, key: str) -> None:
    """Mark *key* as read-only.  Raises KeyError if the key does not exist."""
    if key not in secrets or key.startswith("__"):
        raise KeyError(f"Key '{key}' not found in vault.")
    index = _get_readonly_index(secrets)
    index[key] = True
    _set_readonly_index(secrets, index)


def unprotect(secrets: dict, key: str) -> None:
    """Remove read-only protection from *key*.  No-op if not protected."""
    index = _get_readonly_index(secrets)
    index.pop(key, None)
    _set_readonly_index(secrets, index)


def is_protected(secrets: dict, key: str) -> bool:
    """Return True if *key* is currently read-only."""
    return _get_readonly_index(secrets).get(key, False)


def list_protected(secrets: dict) -> List[str]:
    """Return a sorted list of all currently protected keys."""
    return sorted(k for k, v in _get_readonly_index(secrets).items() if v)


def guard_write(secrets: dict, key: str) -> None:
    """Raise ReadOnlyViolationError if *key* is protected.

    Call this before any mutating operation on a secret.
    """
    if is_protected(secrets, key):
        raise ReadOnlyViolationError(
            f"Secret '{key}' is read-only and cannot be modified. "
            "Use 'envault readonly unprotect' to remove protection first."
        )
