"""CLI tests for the quota commands."""

from __future__ import annotations

import os
import pytest
from click.testing import CliRunner
from envault.vault import Vault
from envault.cli_quota import quota_group


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path), "password")
    v.save({"API_KEY": "abc", "DB_PASS": "xyz"})
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        quota_group,
        ["--vault-dir", vault_dir, "--password", "password", *args],
        catch_exceptions=False,
    )


def test_set_max_secrets_succeeds(runner, vault_dir):
    result = _invoke(runner, vault_dir, "set", "--max-secrets", "50")
    assert result.exit_code == 0
    assert "updated" in result.output.lower()


def test_set_max_value_bytes_succeeds(runner, vault_dir):
    result = _invoke(runner, vault_dir, "set", "--max-value-bytes", "1024")
    assert result.exit_code == 0


def test_set_no_options_fails(runner, vault_dir):
    result = runner.invoke(
        quota_group,
        ["--vault-dir", vault_dir, "--password", "password", "set"],
    )
    assert result.exit_code != 0


def test_show_displays_defaults(runner, vault_dir):
    result = _invoke(runner, vault_dir, "show")
    assert result.exit_code == 0
    assert "max_secrets" in result.output
    assert "max_value_bytes" in result.output


def test_show_reflects_set_value(runner, vault_dir):
    _invoke(runner, vault_dir, "set", "--max-secrets", "42")
    result = _invoke(runner, vault_dir, "show")
    assert "42" in result.output


def test_status_shows_usage(runner, vault_dir):
    result = _invoke(runner, vault_dir, "status")
    assert result.exit_code == 0
    assert "2" in result.output  # 2 secrets
    assert "%" in result.output


def test_status_remaining_slots(runner, vault_dir):
    _invoke(runner, vault_dir, "set", "--max-secrets", "10")
    result = _invoke(runner, vault_dir, "status")
    assert "8" in result.output  # 10 - 2 = 8 remaining
