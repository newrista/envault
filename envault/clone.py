"""Clone secrets between vaults, optionally filtered by tag, group, or key pattern."""

from __future__ import annotations

import fnmatch
from typing import Optional

from envault.vault import Vault
from envault.audit import record_event

_INTERNAL_PREFIX = "__"


def _is_internal(key: str) -> bool:
    return key.startswith(_INTERNAL_PREFIX)


def _matches_pattern(key: str, pattern: Optional[str]) -> bool:
    if pattern is None:
        return True
    return fnmatch.fnmatch(key, pattern)


def clone_secrets(
    src_vault: Vault,
    dst_vault: Vault,
    *,
    pattern: Optional[str] = None,
    keys: Optional[list[str]] = None,
    overwrite: bool = False,
) -> dict[str, str]:
    """Copy secrets from *src_vault* into *dst_vault*.

    Parameters
    ----------
    src_vault:
        Loaded source vault.
    dst_vault:
        Loaded destination vault (will be saved after cloning).
    pattern:
        Optional glob pattern to restrict which keys are copied.
    keys:
        Explicit list of keys to copy; takes precedence over *pattern*.
    overwrite:
        If False (default) existing keys in the destination are skipped.

    Returns
    -------
    dict mapping each copied key to ``"copied"`` or ``"skipped"``.
    """
    src_secrets = src_vault.secrets
    dst_secrets = dst_vault.secrets

    candidates: list[str]
    if keys is not None:
        missing = [k for k in keys if k not in src_secrets]
        if missing:
            raise KeyError(f"Keys not found in source vault: {missing}")
        candidates = list(keys)
    else:
        candidates = [
            k for k in src_secrets
            if not _is_internal(k) and _matches_pattern(k, pattern)
        ]

    result: dict[str, str] = {}
    for key in candidates:
        if key in dst_secrets and not overwrite:
            result[key] = "skipped"
            continue
        dst_secrets[key] = src_secrets[key]
        result[key] = "copied"

    dst_vault.secrets = dst_secrets
    dst_vault.save()

    copied_keys = [k for k, v in result.items() if v == "copied"]
    if copied_keys:
        record_event(
            dst_vault.vault_dir,
            action="clone",
            detail={"source": str(src_vault.vault_dir), "keys": copied_keys},
        )

    return result
