"""CLI tests for envault.cli_remind."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from envault.vault import Vault
from envault.cli_remind import remind_group
from envault.ttl import set_ttl
from envault.rotation import set_rotation_metadata


PASSWORD = "test-password"


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    vault = Vault(str(tmp_path))
    vault.save({"API_KEY": "abc", "DB_PASS": "secret"}, PASSWORD)
    return tmp_path


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        remind_group,
        ["--vault-dir", str(vault_dir), "--password", PASSWORD, *args],
        catch_exceptions=False,
    )


def test_expiring_no_secrets(runner, vault_dir):
    result = runner.invoke(
        remind_group,
        ["expiring", "--vault-dir", str(vault_dir), "--password", PASSWORD],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "No secrets expiring" in result.output


def test_expiring_shows_key(runner, vault_dir):
    vault = Vault(str(vault_dir))
    secrets = vault.load(PASSWORD)
    expiry = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    set_ttl(secrets, "API_KEY", expiry)
    vault.save(secrets, PASSWORD)

    result = runner.invoke(
        remind_group,
        ["expiring", "--vault-dir", str(vault_dir), "--password", PASSWORD],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "API_KEY" in result.output


def test_stale_no_secrets(runner, vault_dir):
    result = runner.invoke(
        remind_group,
        ["stale", "--vault-dir", str(vault_dir), "--password", PASSWORD],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "No secrets are overdue" in result.output


def test_report_shows_both_sections(runner, vault_dir):
    result = runner.invoke(
        remind_group,
        ["report", "--vault-dir", str(vault_dir), "--password", PASSWORD],
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert "Expiring Soon" in result.output
    assert "Rotation Overdue" in result.output
