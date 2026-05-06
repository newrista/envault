"""Human-friendly labels (display names) for secret keys."""

from __future__ import annotations

from typing import Dict, Optional

_LABELS_KEY = "__labels__"


def _get_labels_index(secrets: dict) -> Dict[str, str]:
    """Return the labels index dict from secrets."""
    return secrets.get(_LABELS_KEY, {})


def _set_labels_index(secrets: dict, index: Dict[str, str]) -> None:
    """Persist the labels index back into secrets."""
    secrets[_LABELS_KEY] = index


def set_label(secrets: dict, key: str, label: str) -> None:
    """Attach a human-friendly label to *key*.

    Raises:
        KeyError: if *key* does not exist in secrets.
        ValueError: if *label* is empty or blank.
    """
    if key.startswith("__"):
        raise KeyError(f"Cannot label internal key: {key!r}")
    if key not in secrets:
        raise KeyError(f"Key not found: {key!r}")
    label = label.strip()
    if not label:
        raise ValueError("Label must not be empty.")
    index = _get_labels_index(secrets)
    index[key] = label
    _set_labels_index(secrets, index)


def get_label(secrets: dict, key: str) -> Optional[str]:
    """Return the label for *key*, or ``None`` if not set."""
    return _get_labels_index(secrets).get(key)


def remove_label(secrets: dict, key: str) -> None:
    """Remove the label for *key* (no-op if none exists).

    Raises:
        KeyError: if *key* does not exist in secrets.
    """
    if key not in secrets:
        raise KeyError(f"Key not found: {key!r}")
    index = _get_labels_index(secrets)
    index.pop(key, None)
    _set_labels_index(secrets, index)


def list_labels(secrets: dict) -> Dict[str, str]:
    """Return a mapping of key -> label for all labelled keys."""
    return dict(_get_labels_index(secrets))
