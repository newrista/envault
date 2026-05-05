"""Tests for envault.cli_checkpoint."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_checkpoint import checkpoint_group


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


def _make_vault(vault_dir, secrets, password="pass"):
    v = Vault(str(vault_dir), password)
    v.save(secrets)
    return v


def _invoke(runner, vault_dir, *args, password="pass"):
    return runner.invoke(
        checkpoint_group,
        [*args, "--vault-dir", str(vault_dir), "--password", password],
        catch_exceptions=False,
    )


def test_create_checkpoint_succeeds(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    result = _invoke(runner, vault_dir, "create", "snap1")
    assert result.exit_code == 0
    assert "snap1" in result.output


def test_create_checkpoint_with_description(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    result = _invoke(runner, vault_dir, "create", "snap1", "-d", "my desc")
    assert result.exit_code == 0


def test_list_shows_no_checkpoints(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    result = _invoke(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "No checkpoints" in result.output


def test_list_shows_created_checkpoint(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    _invoke(runner, vault_dir, "create", "release1")
    result = _invoke(runner, vault_dir, "list")
    assert "release1" in result.output


def test_delete_checkpoint_succeeds(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    _invoke(runner, vault_dir, "create", "snap1")
    result = _invoke(runner, vault_dir, "delete", "snap1")
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_diff_shows_no_changes(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    _invoke(runner, vault_dir, "create", "snap1")
    result = _invoke(runner, vault_dir, "diff", "snap1")
    assert result.exit_code == 0
    assert "No changes" in result.output


def test_diff_shows_added_key(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "val"})
    _invoke(runner, vault_dir, "create", "snap1")
    # Add a new key and re-save
    v = Vault(str(vault_dir), "pass")
    secrets = v.load()
    secrets["NEW_KEY"] = "newval"
    v.save(secrets)
    result = _invoke(runner, vault_dir, "diff", "snap1")
    assert "NEW_KEY" in result.output
    assert "+" in result.output
