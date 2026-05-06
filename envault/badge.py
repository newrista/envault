"""Badge generation for vault secrets — produce status shields for README or CI."""

from __future__ import annotations

from typing import Any

from envault.ttl import is_expired, get_ttl
from envault.pin import is_pinned
from envault.schema import get_schema
from envault.lint import lint_secrets

# Badge colour constants
_GREEN = "brightgreen"
_YELLOW = "yellow"
_RED = "red"
_BLUE = "blue"
_GREY = "lightgrey"


def _shield_url(label: str, message: str, colour: str) -> str:
    """Return a shields.io badge URL."""
    label_enc = label.replace("-", "--").replace("_", "__").replace(" ", "_")
    message_enc = message.replace("-", "--").replace("_", "__").replace(" ", "_")
    return f"https://img.shields.io/badge/{label_enc}-{message_enc}-{colour}"


def secret_status_badge(secrets: dict[str, Any], key: str) -> dict[str, str]:
    """Return badge metadata for a single secret key.

    Returns a dict with ``label``, ``message``, ``colour``, and ``url``.
    Raises ``KeyError`` if *key* is not present in *secrets*.
    """
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in vault")

    if is_expired(secrets, key):
        colour, message = _RED, "expired"
    elif get_ttl(secrets, key) is not None:
        colour, message = _YELLOW, "ttl-set"
    elif is_pinned(secrets, key):
        colour, message = _BLUE, "pinned"
    elif get_schema(secrets, key) is not None:
        colour, message = _GREEN, "validated"
    else:
        colour, message = _GREY, "unmanaged"

    url = _shield_url(key, message, colour)
    return {"label": key, "message": message, "colour": colour, "url": url}


def vault_health_badge(secrets: dict[str, Any]) -> dict[str, str]:
    """Return an aggregate health badge for the entire vault."""
    report = lint_secrets(secrets)
    error_count = len(report.errors())
    warning_count = len(report.warnings())

    if error_count > 0:
        colour = _RED
        message = f"{error_count}_error{'s' if error_count != 1 else ''}"
    elif warning_count > 0:
        colour = _YELLOW
        message = f"{warning_count}_warning{'s' if warning_count != 1 else ''}"
    else:
        colour = _GREEN
        message = "healthy"

    url = _shield_url("vault", message, colour)
    return {"label": "vault", "message": message, "colour": colour, "url": url}


def generate_badges(secrets: dict[str, Any], keys: list[str] | None = None) -> list[dict[str, str]]:
    """Generate badge metadata for *keys* (or all non-internal keys)."""
    target_keys = keys if keys is not None else [
        k for k in secrets if not k.startswith("__")
    ]
    return [secret_status_badge(secrets, k) for k in target_keys]
