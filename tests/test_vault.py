"""Unit tests for envault.vault Vault class."""

import pytest
from pathlib import Path
from envault.vault import Vault


PASSWORD = "test-vault-password"
SECRETS = {"DB_URL": "postgres://localhost/dev", "API_KEY": "abc123"}


@pytest.fixture
def tmp_vault(tmp_path):
    return Vault("myproject", vault_dir=tmp_path)


def test_vault_does_not_exist_initially(tmp_vault):
    assert not tmp_vault.exists()


def test_save_creates_vault_file(tmp_vault):
    tmp_vault.save(SECRETS, PASSWORD)
    assert tmp_vault.exists()


def test_load_returns_correct_secrets(tmp_vault):
    tmp_vault.save(SECRETS, PASSWORD)
    loaded = tmp_vault.load(PASSWORD)
    assert loaded == SECRETS


def test_load_wrong_password_raises(tmp_vault):
    tmp_vault.save(SECRETS, PASSWORD)
    with pytest.raises(ValueError):
        tmp_vault.load("wrong-password")


def test_load_nonexistent_vault_raises(tmp_vault):
    with pytest.raises(FileNotFoundError):
        tmp_vault.load(PASSWORD)


def test_delete_removes_vault_file(tmp_vault):
    tmp_vault.save(SECRETS, PASSWORD)
    tmp_vault.delete()
    assert not tmp_vault.exists()


def test_list_vaults(tmp_path):
    for name in ("alpha", "beta", "gamma"):
        Vault(name, vault_dir=tmp_path).save({}, PASSWORD)
    names = Vault.list_vaults(vault_dir=tmp_path)
    assert sorted(names) == ["alpha", "beta", "gamma"]


def test_list_vaults_empty_dir(tmp_path):
    assert Vault.list_vaults(vault_dir=tmp_path / "nonexistent") == []
