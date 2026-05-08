"""Secret inheritance: resolve a key by walking a chain of vaults (parent → child)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_INTERNAL_PREFIX = "__"
_INHERIT_KEY = "__inherit_chain__"


def _is_internal(key: str) -> bool:
    return key.startswith(_INTERNAL_PREFIX)


@dataclass
class InheritResult:
    key: str
    value: Any
    source_index: int  # 0 = first (highest-priority) vault
    chain_length: int

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"InheritResult(key={self.key!r}, source_index={self.source_index}, "
            f"chain_length={self.chain_length})"
        )


def get_inherit_chain(secrets: dict) -> list[str]:
    """Return the ordered list of parent vault paths stored in *secrets*."""
    raw = secrets.get(_INHERIT_KEY, "")
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def set_inherit_chain(secrets: dict, chain: list[str]) -> None:
    """Persist the inheritance chain into *secrets*."""
    secrets[_INHERIT_KEY] = ",".join(chain)


def resolve_inherited(
    key: str,
    vaults: list[dict],
) -> InheritResult:
    """Look up *key* across an ordered list of vault secret dicts.

    The first vault in *vaults* has the highest priority.  Raises
    ``KeyError`` if the key is not found in any vault.
    """
    if _is_internal(key):
        raise ValueError(f"Cannot inherit internal key: {key!r}")
    for idx, vault_secrets in enumerate(vaults):
        if key in vault_secrets:
            return InheritResult(
                key=key,
                value=vault_secrets[key],
                source_index=idx,
                chain_length=len(vaults),
            )
    raise KeyError(f"Key {key!r} not found in any vault in the inheritance chain")


def list_inherited_keys(vaults: list[dict]) -> dict[str, int]:
    """Return a mapping of every non-internal key to the index of the vault
    that would supply its value during resolution."""
    seen: dict[str, int] = {}
    for idx, vault_secrets in enumerate(vaults):
        for k in vault_secrets:
            if not _is_internal(k) and k not in seen:
                seen[k] = idx
    return seen
