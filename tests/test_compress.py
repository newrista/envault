"""Tests for envault.compress."""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from envault.compress import (
    _COMPRESS_MAGIC,
    backup_vault,
    compress_secrets,
    decompress_secrets,
    restore_vault,
)
from envault.vault import Vault


@pytest.fixture()
def tmp_vault(tmp_path: Path) -> Vault:
    vault = Vault(tmp_path)
    vault.save({"API_KEY": "abc123", "DB_PASS": "secret"}, "pw")
    return vault


# --- compress_secrets / decompress_secrets ---


def test_compress_creates_file(tmp_path: Path) -> None:
    dest = tmp_path / "out.gz"
    compress_secrets({"FOO": "bar"}, dest)
    assert dest.exists()


def test_compress_file_is_gzip(tmp_path: Path) -> None:
    dest = tmp_path / "out.gz"
    compress_secrets({"FOO": "bar"}, dest)
    with gzip.open(dest, "rb") as fh:
        data = fh.read()
    assert data.startswith(_COMPRESS_MAGIC)


def test_compress_excludes_internal_keys(tmp_path: Path) -> None:
    dest = tmp_path / "out.gz"
    compress_secrets({"KEY": "val", "__meta": "hidden"}, dest)
    result = decompress_secrets(dest)
    assert "KEY" in result
    assert "__meta" not in result


def test_roundtrip_preserves_secrets(tmp_path: Path) -> None:
    secrets = {"A": "1", "B": "2", "C": "three"}
    dest = tmp_path / "out.gz"
    compress_secrets(secrets, dest)
    assert decompress_secrets(dest) == secrets


def test_decompress_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        decompress_secrets(tmp_path / "nonexistent.gz")


def test_decompress_invalid_magic_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.gz"
    with gzip.open(bad, "wb") as fh:
        fh.write(b"NOT_ENVAULT\n{\"x\": 1}")
    with pytest.raises(ValueError, match="valid envault"):
        decompress_secrets(bad)


# --- backup_vault / restore_vault ---


def test_backup_vault_returns_count(tmp_path: Path, tmp_vault: Vault) -> None:
    dest = tmp_path / "backup.gz"
    n = backup_vault(tmp_vault, "pw", dest)
    assert n == 2


def test_backup_vault_file_readable(tmp_path: Path, tmp_vault: Vault) -> None:
    dest = tmp_path / "backup.gz"
    backup_vault(tmp_vault, "pw", dest)
    result = decompress_secrets(dest)
    assert result["API_KEY"] == "abc123"


def test_restore_vault_merges_secrets(tmp_path: Path, tmp_vault: Vault) -> None:
    dest = tmp_path / "backup.gz"
    compress_secrets({"NEW_KEY": "new_val", "API_KEY": "overridden"}, dest)
    restore_vault(tmp_vault, "pw", dest)
    merged = tmp_vault.load("pw")
    assert merged["NEW_KEY"] == "new_val"
    assert merged["API_KEY"] == "overridden"
    assert merged["DB_PASS"] == "secret"


def test_restore_vault_returns_count(tmp_path: Path, tmp_vault: Vault) -> None:
    dest = tmp_path / "backup.gz"
    compress_secrets({"X": "1", "Y": "2"}, dest)
    n = restore_vault(tmp_vault, "pw", dest)
    assert n == 2
