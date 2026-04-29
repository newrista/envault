"""Group secrets into named collections for batch operations."""

from __future__ import annotations

from typing import Dict, List

_GROUPS_KEY = "__groups__"


def _get_groups_index(secrets: dict) -> Dict[str, List[str]]:
    """Return the groups index stored inside the secrets dict."""
    return secrets.get(_GROUPS_KEY, {})


def _set_groups_index(secrets: dict, index: Dict[str, List[str]]) -> None:
    """Persist the groups index back into the secrets dict."""
    secrets[_GROUPS_KEY] = index


def create_group(secrets: dict, group: str) -> None:
    """Create an empty group if it does not already exist."""
    index = _get_groups_index(secrets)
    if group not in index:
        index[group] = []
    _set_groups_index(secrets, index)


def delete_group(secrets: dict, group: str) -> None:
    """Remove a group entirely (does not delete the underlying secrets)."""
    index = _get_groups_index(secrets)
    if group not in index:
        raise KeyError(f"Group '{group}' does not exist.")
    del index[group]
    _set_groups_index(secrets, index)


def add_to_group(secrets: dict, group: str, key: str) -> None:
    """Add a secret key to a group."""
    real_keys = {k for k in secrets if not k.startswith("__")}
    if key not in real_keys:
        raise KeyError(f"Secret key '{key}' does not exist in the vault.")
    index = _get_groups_index(secrets)
    if group not in index:
        raise KeyError(f"Group '{group}' does not exist. Create it first.")
    if key not in index[group]:
        index[group].append(key)
    _set_groups_index(secrets, index)


def remove_from_group(secrets: dict, group: str, key: str) -> None:
    """Remove a secret key from a group."""
    index = _get_groups_index(secrets)
    if group not in index:
        raise KeyError(f"Group '{group}' does not exist.")
    if key not in index[group]:
        raise KeyError(f"Key '{key}' is not in group '{group}'.")
    index[group].remove(key)
    _set_groups_index(secrets, index)


def get_group_keys(secrets: dict, group: str) -> List[str]:
    """Return all secret keys belonging to a group."""
    index = _get_groups_index(secrets)
    if group not in index:
        raise KeyError(f"Group '{group}' does not exist.")
    return list(index[group])


def list_groups(secrets: dict) -> List[str]:
    """Return all group names defined in the vault."""
    return list(_get_groups_index(secrets).keys())
