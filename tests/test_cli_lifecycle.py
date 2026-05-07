"""Tests for envault.cli_lifecycle CLI commands."""

from __future__ import annotations

import json
import os

import pytest
from click.testing import CliRunner

from envault.cli_lifecycle import lifecycle_group
from envault.vault import Vault

PASSWORD = "test-password"


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture
def runner():
    return CliRunner()


def _make_vault(vault_dir, secrets):
    v = Vault(vault_dir)
    v.save(secrets, PASSWORD)


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        lifecycle_group,
        [*args, "--vault-dir", vault_dir, "--password", PASSWORD],
    )


def test_set_lifecycle_state_succeeds(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    result = _invoke(runner, vault_dir, "set", "API_KEY", "active")
    assert result.exit_code == 0
    assert "active" in result.output


def test_set_lifecycle_state_with_reason(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    result = _invoke(runner, vault_dir, "set", "API_KEY", "deprecated", "--reason", "old")
    assert result.exit_code == 0


def test_set_missing_key_fails(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    result = _invoke(runner, vault_dir, "set", "NOPE", "active")
    assert result.exit_code != 0
    assert "Error" in result.output


def test_show_displays_state(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    _invoke(runner, vault_dir, "set", "API_KEY", "retired", "--reason", "old")
    result = _invoke(runner, vault_dir, "show", "API_KEY")
    assert result.exit_code == 0
    assert "retired" in result.output


def test_show_no_metadata_prints_message(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    result = _invoke(runner, vault_dir, "show", "API_KEY")
    assert result.exit_code == 0
    assert "No lifecycle metadata" in result.output


def test_list_shows_keys_in_state(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc", "TOKEN": "tok"})
    _invoke(runner, vault_dir, "set", "API_KEY", "deprecated")
    _invoke(runner, vault_dir, "set", "TOKEN", "active")
    result = _invoke(runner, vault_dir, "list", "deprecated")
    assert result.exit_code == 0
    assert "API_KEY" in result.output
    assert "TOKEN" not in result.output


def test_list_empty_state_prints_message(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    result = _invoke(runner, vault_dir, "list", "retired")
    assert result.exit_code == 0
    assert "No keys" in result.output


def test_remove_deletes_metadata(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    _invoke(runner, vault_dir, "set", "API_KEY", "active")
    result = _invoke(runner, vault_dir, "remove", "API_KEY")
    assert result.exit_code == 0
    result2 = _invoke(runner, vault_dir, "show", "API_KEY")
    assert "No lifecycle metadata" in result2.output


def test_remove_missing_metadata_fails(runner, vault_dir):
    _make_vault(vault_dir, {"API_KEY": "abc"})
    result = _invoke(runner, vault_dir, "remove", "API_KEY")
    assert result.exit_code != 0
