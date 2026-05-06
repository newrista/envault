"""Integration tests for the favorite CLI commands."""
from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_favorite import favorite_group

PASSWORD = "testpass"


@pytest.fixture()
def vault_dir(tmp_path):
    vault = Vault(str(tmp_path))
    vault.save({"API_KEY": "abc123", "DB_PASS": "secret"}, PASSWORD)
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        favorite_group,
        [*args, "--vault-dir", vault_dir, "--password", PASSWORD],
        catch_exceptions=False,
    )


def test_add_favorite_succeeds(runner, vault_dir):
    result = _invoke(runner, vault_dir, "add", "API_KEY")
    assert result.exit_code == 0
    assert "Added 'API_KEY'" in result.output


def test_add_favorite_with_note(runner, vault_dir):
    result = _invoke(runner, vault_dir, "add", "DB_PASS", "--note", "main db")
    assert result.exit_code == 0


def test_add_favorite_missing_key_fails(runner, vault_dir):
    result = runner.invoke(
        favorite_group,
        ["add", "NO_SUCH_KEY", "--vault-dir", vault_dir, "--password", PASSWORD],
    )
    assert result.exit_code != 0
    assert "NO_SUCH_KEY" in result.output


def test_list_shows_no_favorites_initially(runner, vault_dir):
    result = _invoke(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "No favorites" in result.output


def test_list_shows_added_favorite(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "API_KEY", "--note", "primary")
    result = _invoke(runner, vault_dir, "list")
    assert "API_KEY" in result.output
    assert "primary" in result.output


def test_remove_favorite_succeeds(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "API_KEY")
    result = _invoke(runner, vault_dir, "remove", "API_KEY")
    assert result.exit_code == 0
    assert "Removed 'API_KEY'" in result.output


def test_remove_non_favorite_fails(runner, vault_dir):
    result = runner.invoke(
        favorite_group,
        ["remove", "API_KEY", "--vault-dir", vault_dir, "--password", PASSWORD],
    )
    assert result.exit_code != 0


def test_check_reports_is_favorite(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "DB_PASS")
    result = _invoke(runner, vault_dir, "check", "DB_PASS")
    assert "is a favorite" in result.output


def test_check_reports_not_favorite(runner, vault_dir):
    result = _invoke(runner, vault_dir, "check", "API_KEY")
    assert "NOT a favorite" in result.output
