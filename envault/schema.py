"""Schema validation for vault secrets.

Allows attaching a type/format schema to a secret key so that
values can be validated before being stored or exported.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

# Reserved internal prefix
_SCHEMA_KEY = "__schemas__"

VALID_TYPES = {"string", "integer", "float", "boolean", "url", "email", "regex"}


class SchemaValidationError(ValueError):
    """Raised when a secret value fails schema validation."""


def _get_schema_index(secrets: Dict[str, Any]) -> Dict[str, Any]:
    import json
    raw = secrets.get(_SCHEMA_KEY, "{}")
    return json.loads(raw)


def _set_schema_index(secrets: Dict[str, Any], index: Dict[str, Any]) -> None:
    import json
    secrets[_SCHEMA_KEY] = json.dumps(index)


def set_schema(secrets: Dict[str, Any], key: str, schema_type: str,
               pattern: Optional[str] = None) -> None:
    """Attach a schema rule to *key*.

    Args:
        secrets: The live secrets dict (mutated in place).
        key: The secret key to annotate.
        schema_type: One of VALID_TYPES.
        pattern: Required when schema_type is 'regex'; the pattern to match.
    """
    if key not in secrets or key.startswith("__"):
        raise KeyError(f"Key '{key}' not found in vault")
    if schema_type not in VALID_TYPES:
        raise ValueError(f"Unknown schema type '{schema_type}'. Valid: {sorted(VALID_TYPES)}")
    if schema_type == "regex" and not pattern:
        raise ValueError("'regex' schema type requires a pattern")

    index = _get_schema_index(secrets)
    entry: Dict[str, Any] = {"type": schema_type}
    if pattern:
        entry["pattern"] = pattern
    index[key] = entry
    _set_schema_index(secrets, index)


def get_schema(secrets: Dict[str, Any], key: str) -> Optional[Dict[str, Any]]:
    """Return the schema entry for *key*, or None if not set."""
    return _get_schema_index(secrets).get(key)


def remove_schema(secrets: Dict[str, Any], key: str) -> None:
    """Remove the schema rule for *key* (no-op if not present)."""
    index = _get_schema_index(secrets)
    index.pop(key, None)
    _set_schema_index(secrets, index)


def validate_value(schema: Dict[str, Any], value: str) -> None:
    """Validate *value* against *schema*. Raises SchemaValidationError on failure."""
    stype = schema["type"]
    try:
        if stype == "integer":
            int(value)
        elif stype == "float":
            float(value)
        elif stype == "boolean":
            if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
                raise ValueError
        elif stype == "url":
            if not re.match(r"^https?://", value, re.IGNORECASE):
                raise ValueError
        elif stype == "email":
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", value):
                raise ValueError
        elif stype == "regex":
            if not re.fullmatch(schema["pattern"], value):
                raise ValueError
    except (ValueError, TypeError):
        raise SchemaValidationError(
            f"Value {value!r} does not match schema type '{stype}'"
        )


def validate_all(secrets: Dict[str, Any]) -> Dict[str, str]:
    """Validate every key that has a schema. Returns a dict of {key: error_message}."""
    errors: Dict[str, str] = {}
    index = _get_schema_index(secrets)
    for key, schema in index.items():
        value = secrets.get(key)
        if value is None:
            continue
        try:
            validate_value(schema, value)
        except SchemaValidationError as exc:
            errors[key] = str(exc)
    return errors
