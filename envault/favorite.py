"""Favorite secrets — mark frequently accessed keys for quick retrieval."""
from __future__ import annotations

from typing import Dict, List

_FAVORITES_KEY = "__favorites__"


def _get_favorites(secrets: dict) -> Dict[str, str]:
    """Return the favorites index (key -> optional note)."""
    return dict(secrets.get(_FAVORITES_KEY, {}))


def _set_favorites(secrets: dict, favorites: Dict[str, str]) -> None:
    """Persist the favorites index back into the secrets dict."""
    secrets[_FAVORITES_KEY] = favorites


def add_favorite(secrets: dict, key: str, note: str = "") -> None:
    """Mark *key* as a favorite, optionally storing a short *note*.

    Raises KeyError if *key* does not exist in the vault.
    """
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in vault.")
    if key.startswith("__"):
        raise ValueError(f"Cannot favorite internal key '{key}'.")
    favs = _get_favorites(secrets)
    favs[key] = note.strip()
    _set_favorites(secrets, favs)


def remove_favorite(secrets: dict, key: str) -> None:
    """Remove *key* from favorites.

    Raises KeyError if *key* is not currently a favorite.
    """
    favs = _get_favorites(secrets)
    if key not in favs:
        raise KeyError(f"Key '{key}' is not in favorites.")
    del favs[key]
    _set_favorites(secrets, favs)


def is_favorite(secrets: dict, key: str) -> bool:
    """Return True if *key* is marked as a favorite."""
    return key in _get_favorites(secrets)


def list_favorites(secrets: dict) -> List[Dict[str, str]]:
    """Return a list of dicts with 'key' and 'note' for every favorite."""
    return [
        {"key": k, "note": v}
        for k, v in sorted(_get_favorites(secrets).items())
    ]
