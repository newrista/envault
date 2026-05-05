"""Secret dependency tracking — define which secrets depend on others."""
from __future__ import annotations

from typing import Dict, List

_DEP_KEY = "__dependencies__"


def _get_dep_index(secrets: dict) -> Dict[str, List[str]]:
    """Return the raw dependency index stored inside the vault."""
    return dict(secrets.get(_DEP_KEY, {}))


def _set_dep_index(secrets: dict, index: Dict[str, List[str]]) -> None:
    secrets[_DEP_KEY] = index


def add_dependency(secrets: dict, key: str, depends_on: str) -> None:
    """Record that *key* depends on *depends_on*."""
    if key not in secrets:
        raise KeyError(f"Secret '{key}' does not exist.")
    if depends_on not in secrets:
        raise KeyError(f"Secret '{depends_on}' does not exist.")
    if key == depends_on:
        raise ValueError("A secret cannot depend on itself.")
    index = _get_dep_index(secrets)
    deps = index.get(key, [])
    if depends_on not in deps:
        deps.append(depends_on)
    index[key] = deps
    _set_dep_index(secrets, index)


def remove_dependency(secrets: dict, key: str, depends_on: str) -> None:
    """Remove the dependency of *key* on *depends_on*."""
    index = _get_dep_index(secrets)
    deps = index.get(key, [])
    if depends_on not in deps:
        raise KeyError(f"'{key}' does not depend on '{depends_on}'.")
    deps.remove(depends_on)
    index[key] = deps
    _set_dep_index(secrets, index)


def get_dependencies(secrets: dict, key: str) -> List[str]:
    """Return the list of secrets that *key* directly depends on."""
    return list(_get_dep_index(secrets).get(key, []))


def get_dependents(secrets: dict, key: str) -> List[str]:
    """Return all secrets that depend on *key* (reverse lookup)."""
    index = _get_dep_index(secrets)
    return [k for k, deps in index.items() if key in deps]


def dependency_graph(secrets: dict) -> Dict[str, List[str]]:
    """Return the full dependency graph (key -> list of dependencies)."""
    index = _get_dep_index(secrets)
    return {k: list(v) for k, v in index.items() if v}
