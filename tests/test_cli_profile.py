"""Integration tests for the profile CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_profile import profile_group


PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path))
    v.save({"DB_URL": "postgres://localhost", "API_KEY": "s3cr3t"}, PASSWORD)
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        profile_group,
        ["--vault-dir", vault_dir] + list(args),
        input=f"{PASSWORD}\n{PASSWORD}\n",
        catch_exceptions=False,
    )


def test_create_profile_succeeds(runner, vault_dir):
    result = _invoke(runner, vault_dir, "create", "production")
    assert result.exit_code == 0
    assert "production" in result.output


def test_list_profiles_shows_created(runner, vault_dir):
    _invoke(runner, vault_dir, "create", "staging")
    result = _invoke(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "staging" in result.output


def test_list_profiles_empty(runner, vault_dir):
    result = _invoke(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "No profiles" in result.output


def test_add_and_show_profile_keys(runner, vault_dir):
    _invoke(runner, vault_dir, "create", "prod")
    _invoke(runner, vault_dir, "add", "prod", "DB_URL")
    result = _invoke(runner, vault_dir, "show", "prod")
    assert result.exit_code == 0
    assert "DB_URL" in result.output


def test_show_profile_with_reveal(runner, vault_dir):
    _invoke(runner, vault_dir, "create", "prod")
    _invoke(runner, vault_dir, "add", "prod", "API_KEY")
    result = _invoke(runner, vault_dir, "show", "prod", "--reveal")
    assert result.exit_code == 0
    assert "s3cr3t" in result.output


def test_remove_key_from_profile(runner, vault_dir):
    _invoke(runner, vault_dir, "create", "prod")
    _invoke(runner, vault_dir, "add", "prod", "DB_URL")
    result = _invoke(runner, vault_dir, "remove", "prod", "DB_URL")
    assert result.exit_code == 0
    assert "removed" in result.output


def test_delete_profile(runner, vault_dir):
    _invoke(runner, vault_dir, "create", "temp")
    result = _invoke(runner, vault_dir, "delete", "temp")
    assert result.exit_code == 0
    assert "deleted" in result.output


def test_delete_nonexistent_profile_fails(runner, vault_dir):
    result = runner.invoke(
        profile_group,
        ["--vault-dir", vault_dir, "delete", "ghost"],
        input=f"{PASSWORD}\n{PASSWORD}\n",
    )
    assert result.exit_code != 0
