"""Integration tests for the access CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from envault.cli_access import access_group
from envault.vault import Vault


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path), "testpass")
    v.save({"DB_HOST": "localhost", "API_KEY": "abc"})
    return tmp_path


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, args, vault_dir):
    return runner.invoke(
        access_group,
        args + ["--vault-dir", str(vault_dir), "--password", "testpass"],
        catch_exceptions=False,
    )


def test_set_and_get_permission(runner, vault_dir):
    result = _invoke(runner, ["set", "DB_HOST", "read"], vault_dir)
    assert result.exit_code == 0
    assert "DB_HOST" in result.output

    result = _invoke(runner, ["get", "DB_HOST"], vault_dir)
    assert result.exit_code == 0
    assert "read" in result.output


def test_set_invalid_permission_fails(runner, vault_dir):
    result = runner.invoke(
        access_group,
        ["set", "DB_HOST", "execute", "--vault-dir", str(vault_dir), "--password", "testpass"],
    )
    assert result.exit_code != 0


def test_list_shows_rules(runner, vault_dir):
    _invoke(runner, ["set", "API_KEY", "read", "deny"], vault_dir)
    result = _invoke(runner, ["list"], vault_dir)
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_list_empty_vault(runner, vault_dir):
    result = _invoke(runner, ["list"], vault_dir)
    assert result.exit_code == 0
    assert "No explicit" in result.output


def test_remove_existing_rule(runner, vault_dir):
    _invoke(runner, ["set", "DB_HOST", "read"], vault_dir)
    result = _invoke(runner, ["remove", "DB_HOST"], vault_dir)
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_nonexistent_rule(runner, vault_dir):
    result = _invoke(runner, ["remove", "GHOST_KEY"], vault_dir)
    assert result.exit_code == 0
    assert "No explicit rule" in result.output
