"""Rollback secrets to a previous history entry or checkpoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.history import get_history
from envault.checkpoint import get_checkpoint, list_checkpoints
from envault.readonly import is_protected


@dataclass
class RollbackResult:
    restored: Dict[str, str] = field(default_factory=dict)
    skipped: Dict[str, str] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RollbackResult(restored={len(self.restored)}, skipped={len(self.skipped)})"
        )


def _is_internal(key: str) -> bool:
    return key.startswith("__") and key.endswith("__")


def rollback_to_history(secrets: dict, key: str, steps: int = 1) -> RollbackResult:
    """Restore *key* to the value it held *steps* versions ago."""
    result = RollbackResult()

    if _is_internal(key):
        raise KeyError(f"Cannot rollback internal key: {key}")
    if key not in secrets:
        raise KeyError(f"Key not found in vault: {key}")
    if is_protected(secrets, key):
        result.skipped[key] = "read-only"
        return result

    history = get_history(secrets, key)
    if not history:
        raise ValueError(f"No history available for key: {key}")
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if steps > len(history):
        raise ValueError(
            f"Only {len(history)} history entries available for '{key}'; "
            f"requested {steps}"
        )

    target = history[-steps]
    secrets[key] = target["value"]
    result.restored[key] = target["value"]
    return result


def rollback_to_checkpoint(secrets: dict, name: str) -> RollbackResult:
    """Restore all keys captured in *name* checkpoint."""
    result = RollbackResult()

    cp = get_checkpoint(secrets, name)
    if cp is None:
        raise KeyError(f"Checkpoint not found: {name}")

    snapshot: Dict[str, str] = cp.get("secrets", {})
    for key, value in snapshot.items():
        if _is_internal(key):
            continue
        if is_protected(secrets, key):
            result.skipped[key] = "read-only"
            continue
        secrets[key] = value
        result.restored[key] = value

    return result


def list_rollback_points(secrets: dict, key: str) -> List[dict]:
    """Return history entries available for rollback for *key*."""
    if key not in secrets and not _is_internal(key):
        raise KeyError(f"Key not found in vault: {key}")
    return get_history(secrets, key)
