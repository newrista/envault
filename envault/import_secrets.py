"""Import secrets into a vault from external formats (.env, JSON, shell)."""

import json
import re
from pathlib import Path
from typing import Dict, Optional


def from_dotenv(content: str) -> Dict[str, str]:
    """Parse a .env file content and return a dict of key-value pairs."""
    secrets = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes if present
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        if key:
            secrets[key] = value
    return secrets


def from_json(content: str) -> Dict[str, str]:
    """Parse a JSON object and return a dict of key-value pairs (string values only)."""
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError("JSON content must be a top-level object.")
    result = {}
    for k, v in data.items():
        if not isinstance(k, str):
            raise ValueError(f"JSON key must be a string, got: {type(k).__name__}")
        result[k] = str(v)
    return result


def from_shell(content: str) -> Dict[str, str]:
    """Parse shell export statements and return a dict of key-value pairs."""
    secrets = {}
    pattern = re.compile(r'^export\s+([A-Za-z_][A-Za-z0-9_]*)=["\']?([^"\'\n]*)["\']?')
    for line in content.splitlines():
        line = line.strip()
        match = pattern.match(line)
        if match:
            key, value = match.group(1), match.group(2)
            secrets[key] = value
    return secrets


def import_secrets(source: str, fmt: Optional[str] = None) -> Dict[str, str]:
    """Auto-detect or use given format to parse secrets from a string.

    Args:
        source: Raw file content as a string.
        fmt: One of 'dotenv', 'json', 'shell'. If None, auto-detected.

    Returns:
        Dict of secret key-value pairs.
    """
    if fmt is None:
        stripped = source.strip()
        if stripped.startswith("{"):
            fmt = "json"
        elif re.search(r'^export\s+', source, re.MULTILINE):
            fmt = "shell"
        else:
            fmt = "dotenv"

    parsers = {
        "dotenv": from_dotenv,
        "json": from_json,
        "shell": from_shell,
    }
    if fmt not in parsers:
        raise ValueError(f"Unsupported format: {fmt!r}. Choose from: {list(parsers)}.")
    return parsers[fmt](source)
