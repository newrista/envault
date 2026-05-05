"""Merge secrets from one vault into another with configurable conflict resolution."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, NamedTuple, Optional

INTERNAL_PREFIX = "__"


class ConflictStrategy(str, Enum):
    KEEP = "keep"      # keep destination value on conflict
    OVERWRITE = "overwrite"  # overwrite destination with source value
    SKIP = "skip"      # skip keys that already exist in destination


class MergeResult(NamedTuple):
    added: List[str]
    overwritten: List[str]
    skipped: List[str]
    errors: List[str]


def _is_internal(key: str) -> bool:
    return key.startswith(INTERNAL_PREFIX)


def merge_secrets(
    src: Dict[str, str],
    dst: Dict[str, str],
    strategy: ConflictStrategy = ConflictStrategy.KEEP,
    keys: Optional[List[str]] = None,
    prefix: Optional[str] = None,
) -> MergeResult:
    """Merge secrets from *src* into *dst* in-place.

    Args:
        src: Source secrets dict.
        dst: Destination secrets dict (mutated in-place).
        strategy: How to handle keys that exist in both vaults.
        keys: Optional explicit list of keys to merge; merges all if None.
        prefix: Optional prefix filter — only merge keys starting with this string.

    Returns:
        A :class:`MergeResult` summarising what happened.
    """
    added: List[str] = []
    overwritten: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    candidates = keys if keys is not None else [
        k for k in src if not _is_internal(k)
    ]

    for key in candidates:
        if _is_internal(key):
            errors.append(f"{key}: cannot merge internal key")
            continue
        if key not in src:
            errors.append(f"{key}: not found in source vault")
            continue
        if prefix and not key.startswith(prefix):
            skipped.append(key)
            continue

        if key in dst:
            if strategy == ConflictStrategy.OVERWRITE:
                dst[key] = src[key]
                overwritten.append(key)
            else:
                # KEEP or SKIP both leave destination unchanged
                skipped.append(key)
        else:
            dst[key] = src[key]
            added.append(key)

    return MergeResult(added=added, overwritten=overwritten, skipped=skipped, errors=errors)
