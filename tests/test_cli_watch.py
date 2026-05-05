"""Tests for envault.cli_watch."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.cli_watch import watch_group
from envault.vault import Vault
from envault.watch import _secret_fingerprint, save_watch_state


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _invoke(runner, vault_dir, cmd, password="pass"):
    return runner.invoke(
        watch_group,
        [cmd, "--vault-dir", str(vault_dir), "--password", password],
    )


def _make_vault(vault_dir, secrets, password="pass"):
    vault = Vault(str(vault_dir))
    vault.save(secrets, password)
    return vault


# ---------------------------------------------------------------------------

def test_snapshot_records_baseline(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "value"})
    result = _invoke(runner, vault_dir, "snapshot")
    assert result.exit_code == 0
    assert "baseline recorded" in result.output.lower()

    vault = Vault(str(vault_dir))
    secrets = vault.load("pass")
    assert "__watch_state__" in secrets


def test_check_no_changes(runner, vault_dir):
    secrets = {"KEY": "value"}
    vault = _make_vault(vault_dir, secrets)
    # Record baseline then check immediately
    _invoke(runner, vault_dir, "snapshot")
    result = _invoke(runner, vault_dir, "check")
    assert result.exit_code == 0
    assert "no changes" in result.output.lower()


def test_check_detects_modification(runner, vault_dir):
    vault = _make_vault(vault_dir, {"KEY": "old"})
    _invoke(runner, vault_dir, "snapshot")

    # Modify the secret outside the CLI
    secrets = vault.load("pass")
    secrets["KEY"] = "new"
    vault.save(secrets, "pass")

    result = _invoke(runner, vault_dir, "check")
    assert result.exit_code == 0
    assert "KEY" in result.output
    assert "MODIFIED" in result.output


def test_reset_clears_baseline(runner, vault_dir):
    _make_vault(vault_dir, {"KEY": "value"})
    _invoke(runner, vault_dir, "snapshot")
    result = _invoke(runner, vault_dir, "reset")
    assert result.exit_code == 0
    assert "cleared" in result.output.lower()

    vault = Vault(str(vault_dir))
    secrets = vault.load("pass")
    assert "__watch_state__" not in secrets
