"""Tests for envault.clone module."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.clone import clone_secrets


PASSWORD = "test-pass"


@pytest.fixture()
def src_vault(tmp_path):
    vault_dir = tmp_path / "src"
    vault_dir.mkdir()
    v = Vault(str(vault_dir), PASSWORD)
    v.secrets = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "API_KEY": "secret123",
        "__internal": "hidden",
    }
    v.save()
    v.load()
    return v


@pytest.fixture()
def dst_vault(tmp_path):
    vault_dir = tmp_path / "dst"
    vault_dir.mkdir()
    v = Vault(str(vault_dir), PASSWORD)
    v.secrets = {}
    v.save()
    v.load()
    return v


def test_clone_copies_all_non_internal_keys(src_vault, dst_vault):
    result = clone_secrets(src_vault, dst_vault)
    assert result["DB_HOST"] == "copied"
    assert result["DB_PORT"] == "copied"
    assert result["API_KEY"] == "copied"
    assert "__internal" not in result


def test_clone_with_glob_pattern(src_vault, dst_vault):
    result = clone_secrets(src_vault, dst_vault, pattern="DB_*")
    assert "DB_HOST" in result
    assert "DB_PORT" in result
    assert "API_KEY" not in result


def test_clone_with_explicit_keys(src_vault, dst_vault):
    result = clone_secrets(src_vault, dst_vault, keys=["API_KEY"])
    assert result["API_KEY"] == "copied"
    assert "DB_HOST" not in result


def test_clone_skips_existing_without_overwrite(src_vault, dst_vault):
    dst_vault.secrets["DB_HOST"] = "other"
    dst_vault.save()
    result = clone_secrets(src_vault, dst_vault)
    assert result["DB_HOST"] == "skipped"
    assert dst_vault.secrets["DB_HOST"] == "other"


def test_clone_overwrites_when_flag_set(src_vault, dst_vault):
    dst_vault.secrets["DB_HOST"] = "other"
    dst_vault.save()
    result = clone_secrets(src_vault, dst_vault, overwrite=True)
    assert result["DB_HOST"] == "copied"
    assert dst_vault.secrets["DB_HOST"] == "localhost"


def test_clone_missing_explicit_key_raises(src_vault, dst_vault):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        clone_secrets(src_vault, dst_vault, keys=["MISSING_KEY"])


def test_clone_persists_to_dst_vault(src_vault, dst_vault, tmp_path):
    clone_secrets(src_vault, dst_vault, keys=["DB_HOST"])
    reloaded = Vault(dst_vault.vault_dir, PASSWORD)
    reloaded.load()
    assert reloaded.secrets["DB_HOST"] == "localhost"
