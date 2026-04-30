"""Pin management: lock a secret to a specific version, preventing rotation."""

from __future__ import annotations

from typing import Any

_PINS_KEY = "__pins__"


def _get_pins(secrets: dict[str, Any]) -> dict[str, str]:
    """Return the pins index from the secrets dict."""
    return secrets.get(_PINS_KEY, {})


def _set_pins(secrets: dict[str, Any], pins: dict[str, str]) -> None:
    """Write the pins index back into the secrets dict."""
    secrets[_PINS_KEY] = pins


def pin_secret(secrets: dict[str, Any], key: str, reason: str = "") -> None:
    """Pin *key* to its current value, storing an optional reason.

    Raises KeyError if the key does not exist in the vault.
    """
    if key not in secrets or key.startswith("__"):
        raise KeyError(f"Secret '{key}' not found in vault.")
    pins = _get_pins(secrets)
    pins[key] = reason
    _set_pins(secrets, pins)


def unpin_secret(secrets: dict[str, Any], key: str) -> None:
    """Remove the pin from *key*.

    Raises KeyError if the key is not currently pinned.
    """
    pins = _get_pins(secrets)
    if key not in pins:
        raise KeyError(f"Secret '{key}' is not pinned.")
    del pins[key]
    _set_pins(secrets, pins)


def is_pinned(secrets: dict[str, Any], key: str) -> bool:
    """Return True if *key* is pinned."""
    return key in _get_pins(secrets)


def get_pin_reason(secrets: dict[str, Any], key: str) -> str | None:
    """Return the pin reason for *key*, or None if not pinned."""
    return _get_pins(secrets).get(key)


def list_pinned(secrets: dict[str, Any]) -> dict[str, str]:
    """Return a mapping of {key: reason} for all pinned secrets."""
    return dict(_get_pins(secrets))
