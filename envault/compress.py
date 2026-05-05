"""Vault compression: gzip-compress/decompress secret exports for backup or transfer."""

from __future__ import annotations

import gzip
import json
import os
from pathlib import Path
from typing import Dict

from envault.vault import Vault

_COMPRESS_MAGIC = b"ENVAULT_GZ_V1"


def compress_secrets(secrets: Dict[str, str], dest: Path) -> int:
    """Write secrets as a gzip-compressed JSON blob to *dest*.

    Returns the number of secrets written.
    """
    payload = {
        k: v
        for k, v in secrets.items()
        if not k.startswith("__")
    }
    raw = json.dumps(payload, sort_keys=True).encode()
    with gzip.open(dest, "wb") as fh:
        fh.write(_COMPRESS_MAGIC + b"\n" + raw)
    return len(payload)


def decompress_secrets(src: Path) -> Dict[str, str]:
    """Read a compressed secrets file produced by :func:`compress_secrets`.

    Raises ``ValueError`` if the file does not look like an envault archive.
    """
    if not src.exists():
        raise FileNotFoundError(f"Compressed archive not found: {src}")
    with gzip.open(src, "rb") as fh:
        data = fh.read()
    if not data.startswith(_COMPRESS_MAGIC):
        raise ValueError(f"Not a valid envault compressed archive: {src}")
    json_bytes = data[len(_COMPRESS_MAGIC) + 1 :]
    return json.loads(json_bytes.decode())


def backup_vault(vault: Vault, password: str, dest: Path) -> int:
    """Load *vault* with *password* and write a compressed backup to *dest*.

    Returns the number of secrets backed up.
    """
    secrets = vault.load(password)
    return compress_secrets(secrets, dest)


def restore_vault(vault: Vault, password: str, src: Path) -> int:
    """Restore secrets from a compressed backup *src* into *vault*.

    Existing secrets are merged (backup values win on conflict).
    Returns the number of secrets restored.
    """
    incoming = decompress_secrets(src)
    try:
        existing = vault.load(password)
    except Exception:
        existing = {}
    merged = {**existing, **incoming}
    vault.save(merged, password)
    return len(incoming)
