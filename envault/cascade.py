"""Cascade resolution: merge secrets from multiple vaults in priority order."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

INTERNAL_PREFIX = "__"


def _is_internal(key: str) -> bool:
    return key.startswith(INTERNAL_PREFIX)


class CascadeResult:
    """Result of a cascade resolution."""

    def __init__(
        self,
        resolved: Dict[str, str],
        sources: Dict[str, str],
    ) -> None:
        self.resolved = resolved  # key -> final value
        self.sources = sources    # key -> vault path that provided the value

    def __repr__(self) -> str:  # pragma: no cover
        return f"CascadeResult(keys={list(self.resolved.keys())})"


def cascade_resolve(
    layers: List[Tuple[str, Dict[str, str]]],
    keys: Optional[List[str]] = None,
) -> CascadeResult:
    """Resolve secrets from multiple vault layers in priority order.

    Args:
        layers: List of (vault_path, secrets_dict) tuples ordered from
                *lowest* to *highest* priority. Higher-priority layers
                override lower-priority ones.
        keys:   Optional list of specific keys to resolve. If None, all
                non-internal keys from all layers are considered.

    Returns:
        CascadeResult with the merged secrets and their originating vault.
    """
    if not layers:
        return CascadeResult({}, {})

    # Collect candidate keys
    if keys is not None:
        candidate_keys: List[str] = keys
    else:
        candidate_keys = []
        seen: set = set()
        for _, secrets in layers:
            for k in secrets:
                if not _is_internal(k) and k not in seen:
                    candidate_keys.append(k)
                    seen.add(k)

    resolved: Dict[str, str] = {}
    sources: Dict[str, str] = {}

    for key in candidate_keys:
        # Iterate highest-priority last, so last write wins
        for vault_path, secrets in layers:
            if key in secrets and not _is_internal(key):
                resolved[key] = secrets[key]
                sources[key] = vault_path

    return CascadeResult(resolved, sources)


def list_overrides(
    layers: List[Tuple[str, Dict[str, str]]],
) -> Dict[str, List[Tuple[str, str]]]:
    """Return every key that appears in more than one layer, with all its values.

    Returns a dict mapping key -> [(vault_path, value), ...] ordered low-to-high.
    Only keys with at least two occurrences are included.
    """
    occurrences: Dict[str, List[Tuple[str, str]]] = {}
    for vault_path, secrets in layers:
        for key, value in secrets.items():
            if _is_internal(key):
                continue
            occurrences.setdefault(key, []).append((vault_path, value))
    return {k: v for k, v in occurrences.items() if len(v) > 1}
