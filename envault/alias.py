"""Alias management for vault secret keys."""

from __future__ import annotations

from typing import Dict, Optional

ALIAS_INDEX_KEY = "__aliases__"


def _get_alias_index(secrets: dict) -> Dict[str, str]:
    """Return the alias -> canonical_key mapping stored in secrets."""
    return dict(secrets.get(ALIAS_INDEX_KEY, {}))


def _set_alias_index(secrets: dict, index: Dict[str, str]) -> None:
    """Persist the alias index back into the secrets dict."""
    secrets[ALIAS_INDEX_KEY] = index


def add_alias(secrets: dict, alias: str, key: str) -> None:
    """Create *alias* pointing to *key*.

    Raises KeyError if *key* does not exist in the vault.
    Raises ValueError if *alias* clashes with an existing real key or
    reserved key.
    """
    if alias == ALIAS_INDEX_KEY:
        raise ValueError(f"'{alias}' is a reserved key.")
    if alias in secrets and alias != ALIAS_INDEX_KEY:
        raise ValueError(f"'{alias}' already exists as a secret key.")
    if key not in secrets or key == ALIAS_INDEX_KEY:
        raise KeyError(f"Secret '{key}' not found in vault.")

    index = _get_alias_index(secrets)
    if alias in index:
        raise ValueError(f"'{alias}' already exists as an alias for '{index[alias]}'.")
    index[alias] = key
    _set_alias_index(secrets, index)


def remove_alias(secrets: dict, alias: str) -> None:
    """Remove *alias*. Raises KeyError if alias does not exist."""
    index = _get_alias_index(secrets)
    if alias not in index:
        raise KeyError(f"Alias '{alias}' not found.")
    del index[alias]
    _set_alias_index(secrets, index)


def resolve_alias(secrets: dict, alias: str) -> Optional[str]:
    """Return the canonical key for *alias*, or None if not an alias."""
    return _get_alias_index(secrets).get(alias)


def list_aliases(secrets: dict) -> Dict[str, str]:
    """Return all alias -> canonical_key mappings."""
    return _get_alias_index(secrets)


def get_via_alias(secrets: dict, alias: str) -> str:
    """Retrieve a secret value using either its real key or an alias.

    Raises KeyError if neither the alias nor the resolved key exists.
    """
    canonical = resolve_alias(secrets, alias)
    lookup_key = canonical if canonical is not None else alias
    if lookup_key not in secrets or lookup_key == ALIAS_INDEX_KEY:
        raise KeyError(f"No secret found for '{alias}'.")
    return secrets[lookup_key]


def rename_alias(secrets: dict, old_alias: str, new_alias: str) -> None:
    """Rename an existing alias from *old_alias* to *new_alias*.

    Raises KeyError if *old_alias* does not exist.
    Raises ValueError if *new_alias* clashes with an existing key, alias,
    or reserved key.
    """
    index = _get_alias_index(secrets)
    if old_alias not in index:
        raise KeyError(f"Alias '{old_alias}' not found.")
    if new_alias == ALIAS_INDEX_KEY:
        raise ValueError(f"'{new_alias}' is a reserved key.")
    if new_alias in secrets:
        raise ValueError(f"'{new_alias}' already exists as a secret key.")
    if new_alias in index:
        raise ValueError(f"'{new_alias}' already exists as an alias for '{index[new_alias]}'.")
    index[new_alias] = index.pop(old_alias)
    _set_alias_index(secrets, index)
