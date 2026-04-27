"""Tests for envault.cli_audit CLI commands."""

import pytest
from click.testing import CliRunner

from envault.cli_audit import audit_group
from envault.audit import record_event


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


def test_log_shows_no_events_message(runner, vault_dir):
    result = runner.invoke(audit_group, ["log", "--vault-dir", vault_dir])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_log_displays_recorded_events(runner, vault_dir):
    record_event(vault_dir, action="set", key="DB_URL", actor="bob")
    result = runner.invoke(audit_group, ["log", "--vault-dir", vault_dir])
    assert result.exit_code == 0
    assert "SET" in result.output
    assert "DB_URL" in result.output
    assert "bob" in result.output


def test_log_filters_by_action(runner, vault_dir):
    record_event(vault_dir, action="set", key="FOO", actor="alice")
    record_event(vault_dir, action="get", key="BAR", actor="alice")
    result = runner.invoke(
        audit_group, ["log", "--vault-dir", vault_dir, "--action", "get"]
    )
    assert result.exit_code == 0
    assert "GET" in result.output
    assert "SET" not in result.output


def test_log_filters_by_key(runner, vault_dir):
    record_event(vault_dir, action="set", key="ALPHA")
    record_event(vault_dir, action="set", key="BETA")
    result = runner.invoke(
        audit_group, ["log", "--vault-dir", vault_dir, "--key", "ALPHA"]
    )
    assert result.exit_code == 0
    assert "ALPHA" in result.output
    assert "BETA" not in result.output


def test_log_respects_limit(runner, vault_dir):
    for i in range(10):
        record_event(vault_dir, action="get", key=f"KEY_{i}")
    result = runner.invoke(
        audit_group, ["log", "--vault-dir", vault_dir, "--limit", "3"]
    )
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().splitlines() if l]
    assert len(lines) == 3


def test_stats_shows_no_events_message(runner, vault_dir):
    result = runner.invoke(audit_group, ["stats", "--vault-dir", vault_dir])
    assert result.exit_code == 0
    assert "No audit events found" in result.output


def test_stats_displays_totals(runner, vault_dir):
    record_event(vault_dir, action="set", key="TOKEN")
    record_event(vault_dir, action="get", key="TOKEN")
    record_event(vault_dir, action="get", key="TOKEN")
    result = runner.invoke(audit_group, ["stats", "--vault-dir", vault_dir])
    assert result.exit_code == 0
    assert "Total events: 3" in result.output
    assert "get: 2" in result.output
    assert "set: 1" in result.output
    assert "TOKEN" in result.output
