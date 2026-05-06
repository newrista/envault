"""Redaction utilities for masking sensitive secret values in output."""

from __future__ import annotations

import re
from typing import Dict, List, Optional

_INTERNAL_PREFIX = "__"
_DEFAULT_MASK = "****"
_DEFAULT_REVEAL_CHARS = 0


def _is_internal(key: str) -> bool:
    return key.startswith(_INTERNAL_PREFIX)


def mask_value(
    value: str,
    mask: str = _DEFAULT_MASK,
    reveal_chars: int = _DEFAULT_REVEAL_CHARS,
) -> str:
    """Return a masked version of *value*.

    If *reveal_chars* > 0, the last N characters of the value are kept visible.
    """
    if not value:
        return mask
    if reveal_chars > 0 and len(value) > reveal_chars:
        return mask + value[-reveal_chars:]
    return mask


def redact_secrets(
    secrets: Dict[str, str],
    keys: Optional[List[str]] = None,
    mask: str = _DEFAULT_MASK,
    reveal_chars: int = _DEFAULT_REVEAL_CHARS,
    skip_internal: bool = True,
) -> Dict[str, str]:
    """Return a copy of *secrets* with values replaced by *mask*.

    Parameters
    ----------
    secrets:
        The source dict of key/value pairs.
    keys:
        If provided, only redact these specific keys; all others are returned
        unchanged.
    mask:
        The replacement string used for masked values.
    reveal_chars:
        Number of trailing characters to leave visible in each masked value.
    skip_internal:
        When *True* (default), keys starting with ``__`` are never redacted.
    """
    target_keys = set(keys) if keys is not None else None
    result: Dict[str, str] = {}
    for key, value in secrets.items():
        if skip_internal and _is_internal(key):
            result[key] = value
        elif target_keys is not None and key not in target_keys:
            result[key] = value
        else:
            result[key] = mask_value(value, mask=mask, reveal_chars=reveal_chars)
    return result


def redact_string(
    text: str,
    secrets: Dict[str, str],
    mask: str = _DEFAULT_MASK,
) -> str:
    """Replace all secret values found in *text* with *mask*.

    Useful for sanitising log lines or command output before display.
    """
    for key, value in secrets.items():
        if _is_internal(key) or not value:
            continue
        text = text.replace(value, mask)
    return text
