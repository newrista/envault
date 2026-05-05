"""Tests for envault.cli_verify CLI commands."""

from __future__ import annotations

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from envault.cli_verify import verify_group
from envault.verify import VerifyReport, VerifyIssue


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, args, **kwargs):
    return runner.invoke(verify_group, args, catch_exceptions=False, **kwargs)


def _make_report(*issues):
    return VerifyReport(issues=list(issues))


def test_run_no_vault_exits_with_error(runner, tmp_path):
    result = _invoke(runner, ["run", "--vault-dir", str(tmp_path), "--password", "pw"])
    assert result.exit_code == 1
    assert "No vault found" in result.output


def test_run_all_clear_prints_success(runner, tmp_path):
    with patch("envault.cli_verify.Vault") as MockVault:
        inst = MockVault.return_value
        inst.exists.return_value = True
        inst.load.return_value = {"KEY": "val"}
        with patch("envault.cli_verify.verify_secrets", return_value=_make_report()):
            result = _invoke(runner, ["run", "--vault-dir", str(tmp_path), "--password", "pw"])
    assert result.exit_code == 0
    assert "All checks passed" in result.output


def test_run_shows_errors(runner, tmp_path):
    issue = VerifyIssue(key="DB_PASS", level="error", message="type mismatch")
    with patch("envault.cli_verify.Vault") as MockVault:
        inst = MockVault.return_value
        inst.exists.return_value = True
        inst.load.return_value = {"DB_PASS": "bad"}
        with patch("envault.cli_verify.verify_secrets", return_value=_make_report(issue)):
            result = _invoke(runner, ["run", "--vault-dir", str(tmp_path), "--password", "pw"])
    assert result.exit_code == 1
    assert "DB_PASS" in result.output
    assert "type mismatch" in result.output


def test_run_strict_exits_on_warnings(runner, tmp_path):
    issue = VerifyIssue(key="TOKEN", level="warning", message="expired")
    with patch("envault.cli_verify.Vault") as MockVault:
        inst = MockVault.return_value
        inst.exists.return_value = True
        inst.load.return_value = {"TOKEN": "x"}
        with patch("envault.cli_verify.verify_secrets", return_value=_make_report(issue)):
            result = _invoke(
                runner,
                ["run", "--vault-dir", str(tmp_path), "--password", "pw", "--strict"],
            )
    assert result.exit_code == 1


def test_run_only_errors_hides_info(runner, tmp_path):
    info = VerifyIssue(key="KEY", level="info", message="No schema defined for key.")
    error = VerifyIssue(key="KEY", level="error", message="bad value")
    with patch("envault.cli_verify.Vault") as MockVault:
        inst = MockVault.return_value
        inst.exists.return_value = True
        inst.load.return_value = {"KEY": "v"}
        with patch("envault.cli_verify.verify_secrets", return_value=_make_report(info, error)):
            result = _invoke(
                runner,
                ["run", "--vault-dir", str(tmp_path), "--password", "pw", "--only-errors"],
            )
    assert "No schema" not in result.output
    assert "bad value" in result.output
