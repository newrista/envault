"""Export module for envault.

Provides utilities to export vault secrets to various formats:
- .env file format
- JSON
- Shell export statements

All exports are done in-memory or to a specified file path.
No plaintext secrets are persisted unless explicitly requested.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


SUPPORTED_FORMATS = ("dotenv", "json", "shell")


def to_dotenv(secrets: Dict[str, str]) -> str:
    """Serialize secrets to .env file format.

    Each entry is written as KEY=VALUE on its own line.
    Values containing spaces or special characters are quoted.

    Args:
        secrets: A dict mapping variable names to their plaintext values.

    Returns:
        A string in .env format.
    """
    lines = []
    for key, value in sorted(secrets.items()):
        # Skip internal rotation metadata keys
        if key.startswith("__"):
            continue
        # Quote values that contain whitespace, quotes, or $ signs
        if any(ch in value for ch in (" ", "\t", '"', "'", "$", "\n")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def to_json(secrets: Dict[str, str], indent: int = 2) -> str:
    """Serialize secrets to a JSON string.

    Args:
        secrets: A dict mapping variable names to their plaintext values.
        indent: JSON indentation level (default 2).

    Returns:
        A pretty-printed JSON string.
    """
    filtered = {k: v for k, v in secrets.items() if not k.startswith("__")}
    return json.dumps(filtered, indent=indent, sort_keys=True)


def to_shell(secrets: Dict[str, str]) -> str:
    """Serialize secrets as shell export statements.

    Suitable for sourcing directly in a shell session::

        source <(envault export --format shell)

    Args:
        secrets: A dict mapping variable names to their plaintext values.

    Returns:
        A string of 'export KEY="VALUE"' lines.
    """
    lines = []
    for key, value in sorted(secrets.items()):
        if key.startswith("__"):
            continue
        escaped = value.replace('"', '\\"')
        lines.append(f'export {key}="{escaped}"')
    return "\n".join(lines) + ("\n" if lines else "")


def export_secrets(
    secrets: Dict[str, str],
    fmt: str = "dotenv",
    output_path: Optional[str] = None,
) -> str:
    """Export secrets in the specified format, optionally writing to a file.

    Args:
        secrets: A dict mapping variable names to their plaintext values.
        fmt: Output format — one of 'dotenv', 'json', or 'shell'.
        output_path: If provided, write the output to this file path.
                     The file will be created with mode 0o600 (owner read/write only).

    Returns:
        The serialized secrets string.

    Raises:
        ValueError: If an unsupported format is requested.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported export format '{fmt}'. "
            f"Choose one of: {', '.join(SUPPORTED_FORMATS)}"
        )

    serializers = {
        "dotenv": to_dotenv,
        "json": to_json,
        "shell": to_shell,
    }

    output = serializers[fmt](secrets)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write with restrictive permissions so secrets aren't world-readable
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(output)

    return output
