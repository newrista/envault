"""Reorder (prioritize/sort) secrets within a vault."""

from __future__ import annotations

from typing import Dict, List, Optional

_INTERNAL_PREFIX = "__"


def _is_internal(key: str) -> bool:
    return key.startswith(_INTERNAL_PREFIX)


def sort_secrets(
    secrets: Dict[str, str],
    *,
    reverse: bool = False,
    case_sensitive: bool = False,
) -> Dict[str, str]:
    """Return a new dict with user secrets sorted alphabetically.

    Internal keys (prefixed with ``__``) are preserved at the end in
    their original relative order.
    """
    user_keys = [k for k in secrets if not _is_internal(k)]
    internal_keys = [k for k in secrets if _is_internal(k)]

    sorted_user = sorted(
        user_keys,
        key=lambda k: k if case_sensitive else k.lower(),
        reverse=reverse,
    )

    return {k: secrets[k] for k in sorted_user + internal_keys}


def move_to_top(
    secrets: Dict[str, str],
    keys: List[str],
) -> Dict[str, str]:
    """Move the given *keys* to the front of the secrets dict.

    Missing keys are silently ignored. Internal keys cannot be moved.
    """
    for key in keys:
        if key not in secrets:
            raise KeyError(f"Key '{key}' not found in vault.")
        if _is_internal(key):
            raise ValueError(f"Cannot reorder internal key '{key}'.")

    pinned = [k for k in keys if k in secrets]
    rest = [k for k in secrets if k not in pinned]
    return {k: secrets[k] for k in pinned + rest}


def move_to_bottom(
    secrets: Dict[str, str],
    keys: List[str],
) -> Dict[str, str]:
    """Move the given *keys* to the end of the user-secrets section.

    Internal keys remain after all user keys.
    """
    for key in keys:
        if key not in secrets:
            raise KeyError(f"Key '{key}' not found in vault.")
        if _is_internal(key):
            raise ValueError(f"Cannot reorder internal key '{key}'.")

    pinned = [k for k in keys if k in secrets]
    user_rest = [k for k in secrets if k not in pinned and not _is_internal(k)]
    internal = [k for k in secrets if _is_internal(k)]
    return {k: secrets[k] for k in user_rest + pinned + internal}


def apply_order(
    secrets: Dict[str, str],
    ordered_keys: List[str],
) -> Dict[str, str]:
    """Reorder secrets according to *ordered_keys*.

    Keys not present in *ordered_keys* are appended in their original
    relative order after the explicitly ordered ones (internal keys last).
    """
    for key in ordered_keys:
        if _is_internal(key):
            raise ValueError(f"Cannot reorder internal key '{key}'.")
        if key not in secrets:
            raise KeyError(f"Key '{key}' not found in vault.")

    remaining_user = [
        k for k in secrets if k not in ordered_keys and not _is_internal(k)
    ]
    internal = [k for k in secrets if _is_internal(k)]
    final_order = ordered_keys + remaining_user + internal
    return {k: secrets[k] for k in final_order}
