"""Tests for envault.cli_rollback."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.history import record_history
from envault.checkpoint import create_checkpoint
from envault.cli_rollback import rollback_group


PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _make_vault(vault_dir: str, secrets: dict) -> None:
    v = Vault(vault_dir)
    v.save(secrets, PASSWORD)


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        rollback_group,
        list(args) + ["--vault-dir", vault_dir, "--password", PASSWORD],
        catch_exceptions=False,
    )


def test_history_rollback_succeeds(runner, vault_dir):
    secrets = {"API_KEY": "v1"}
    record_history(secrets, "API_KEY", "v0")
    record_history(secrets, "API_KEY", "v1")
    _make_vault(vault_dir, secrets)

    result = _invoke(runner, vault_dir, "history", "API_KEY", "--steps", "1")
    assert result.exit_code == 0
    assert "Rolled back" in result.output


def test_history_rollback_missing_key_fails(runner, vault_dir):
    _make_vault(vault_dir, {"X": "y"})
    result = runner.invoke(
        rollback_group,
        ["history", "MISSING", "--vault-dir", vault_dir, "--password", PASSWORD],
    )
    assert result.exit_code != 0


def test_checkpoint_rollback_succeeds(runner, vault_dir):
    secrets = {"FOO": "bar"}
    create_checkpoint(secrets, "snap1")
    _make_vault(vault_dir, secrets)

    result = _invoke(runner, vault_dir, "checkpoint", "snap1")
    assert result.exit_code == 0
    assert "snap1" in result.output


def test_checkpoint_rollback_missing_fails(runner, vault_dir):
    _make_vault(vault_dir, {"FOO": "bar"})
    result = runner.invoke(
        rollback_group,
        ["checkpoint", "ghost", "--vault-dir", vault_dir, "--password", PASSWORD],
    )
    assert result.exit_code != 0


def test_points_cmd_shows_history(runner, vault_dir):
    secrets = {"API_KEY": "v1"}
    record_history(secrets, "API_KEY", "v0")
    record_history(secrets, "API_KEY", "v1")
    _make_vault(vault_dir, secrets)

    result = _invoke(runner, vault_dir, "points", "API_KEY")
    assert result.exit_code == 0
    assert "[1]" in result.output


def test_points_cmd_no_history_shows_message(runner, vault_dir):
    _make_vault(vault_dir, {"BARE": "val"})
    result = _invoke(runner, vault_dir, "points", "BARE")
    assert result.exit_code == 0
    assert "No history" in result.output
