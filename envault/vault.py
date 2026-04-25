"""Vault model: read, write, and manage encrypted vault files on disk."""

import json
import os
from pathlib import Path
from typing import Dict

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_DIR = Path.home() / ".envault" / "vaults"


class Vault:
    """Represents an encrypted key-value store for a named project."""

    def __init__(self, name: str, vault_dir: Path = DEFAULT_VAULT_DIR):
        self.name = name
        self.vault_dir = vault_dir
        self.path = vault_dir / f"{name}.vault"

    def exists(self) -> bool:
        return self.path.exists()

    def save(self, secrets: Dict[str, str], password: str) -> None:
        """Serialize and encrypt secrets, then write to disk."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        plaintext = json.dumps(secrets)
        encrypted = encrypt(plaintext, password)
        self.path.write_bytes(encrypted)

    def load(self, password: str) -> Dict[str, str]:
        """Read from disk, decrypt, and return secrets dict."""
        if not self.exists():
            raise FileNotFoundError(f"Vault '{self.name}' does not exist.")
        data = self.path.read_bytes()
        plaintext = decrypt(data, password)
        return json.loads(plaintext)

    def delete(self) -> None:
        """Permanently remove the vault file."""
        if self.exists():
            self.path.unlink()

    @classmethod
    def list_vaults(cls, vault_dir: Path = DEFAULT_VAULT_DIR) -> list:
        """Return names of all existing vaults."""
        if not vault_dir.exists():
            return []
        return [p.stem for p in vault_dir.glob("*.vault")]
