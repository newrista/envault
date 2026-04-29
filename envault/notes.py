"""Per-secret notes/comments stored alongside vault metadata."""

from __future__ import annotations

from typing import Optional

NOTES_KEY = "__notes__"


def _get_notes_index(secrets: dict) -> dict:
    """Return the notes index stored inside the secrets dict."""
    return secrets.get(NOTES_KEY, {})


def _set_notes_index(secrets: dict, index: dict) -> None:
    """Persist the notes index back into the secrets dict."""
    secrets[NOTES_KEY] = index


def set_note(secrets: dict, key: str, note: str) -> None:
    """Attach a note to *key*.

    Raises KeyError if *key* does not exist in the vault.
    """
    if key not in secrets and key != NOTES_KEY:
        # Allow the caller to check existence before calling us, but guard
        # against typos.
        real_keys = {k for k in secrets if not k.startswith("__")}
        if key not in real_keys:
            raise KeyError(f"Secret '{key}' not found in vault.")

    index = _get_notes_index(secrets)
    index[key] = note
    _set_notes_index(secrets, index)


def get_note(secrets: dict, key: str) -> Optional[str]:
    """Return the note attached to *key*, or None if no note exists."""
    return _get_notes_index(secrets).get(key)


def remove_note(secrets: dict, key: str) -> bool:
    """Remove the note for *key*.

    Returns True if a note was removed, False if none existed.
    """
    index = _get_notes_index(secrets)
    if key in index:
        del index[key]
        _set_notes_index(secrets, index)
        return True
    return False


def list_notes(secrets: dict) -> dict[str, str]:
    """Return a copy of all key → note mappings."""
    return dict(_get_notes_index(secrets))
