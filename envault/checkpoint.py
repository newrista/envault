"""Checkpoint feature: named restore points with metadata for a vault."""

from __future__ import annotations

import time
from typing import Any

CHECKPOINT_KEY = "__checkpoints__"


def _get_checkpoints(secrets: dict) -> dict:
    return secrets.get(CHECKPOINT_KEY, {})


def _set_checkpoints(secrets: dict, checkpoints: dict) -> None:
    secrets[CHECKPOINT_KEY] = checkpoints


def create_checkpoint(secrets: dict, name: str, description: str = "") -> dict:
    """Record a named checkpoint with the current secret keys and a timestamp."""
    if not name or not name.isidentifier():
        raise ValueError(f"Invalid checkpoint name: {name!r}. Must be a valid identifier.")

    user_keys = [k for k in secrets if not k.startswith("__")]
    checkpoints = _get_checkpoints(secrets)
    checkpoints[name] = {
        "created_at": time.time(),
        "description": description,
        "keys": sorted(user_keys),
    }
    _set_checkpoints(secrets, checkpoints)
    return checkpoints[name]


def delete_checkpoint(secrets: dict, name: str) -> None:
    """Remove a named checkpoint."""
    checkpoints = _get_checkpoints(secrets)
    if name not in checkpoints:
        raise KeyError(f"Checkpoint {name!r} does not exist.")
    del checkpoints[name]
    _set_checkpoints(secrets, checkpoints)


def get_checkpoint(secrets: dict, name: str) -> dict:
    """Return metadata for a named checkpoint."""
    checkpoints = _get_checkpoints(secrets)
    if name not in checkpoints:
        raise KeyError(f"Checkpoint {name!r} does not exist.")
    return checkpoints[name]


def list_checkpoints(secrets: dict) -> list[dict]:
    """Return all checkpoints sorted by creation time."""
    checkpoints = _get_checkpoints(secrets)
    return sorted(
        [{"name": n, **meta} for n, meta in checkpoints.items()],
        key=lambda c: c["created_at"],
    )


def diff_from_checkpoint(secrets: dict, name: str) -> dict[str, Any]:
    """Return keys added/removed since the checkpoint was created."""
    cp = get_checkpoint(secrets, name)
    cp_keys = set(cp["keys"])
    current_keys = {k for k in secrets if not k.startswith("__")}
    return {
        "added": sorted(current_keys - cp_keys),
        "removed": sorted(cp_keys - current_keys),
    }
