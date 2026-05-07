"""Tests for envault.cli_scoring CLI commands."""
from __future__ import annotations

import json
import os
import pytest
from click.testing import CliRunner

from envault.cli_scoring import scoring_group
from envault.vault import Vault

PASSWORD = "test-pass"


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path))
    v.save({"API_KEY": "hello", "DB_PASS": "world"}, PASSWORD)
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        scoring_group,
        ["show", "--vault-dir", vault_dir, "--password", PASSWORD, *args],
        catch_exceptions=False,
    )


def test_show_exits_zero(runner, vault_dir):
    result = _invoke(runner, vault_dir)
    assert result.exit_code == 0


def test_show_contains_score(runner, vault_dir):
    result = _invoke(runner, vault_dir)
    assert "Health score" in result.output


def test_show_json_flag_returns_valid_json(runner, vault_dir):
    result = _invoke(runner, vault_dir, "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "score" in data
    assert "grade" in data
    assert "total_keys" in data


def test_show_no_vault_exits_with_error(runner, tmp_path):
    result = runner.invoke(
        scoring_group,
        ["show", "--vault-dir", str(tmp_path), "--password", PASSWORD],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "No vault found" in result.output


def test_show_json_total_keys_correct(runner, vault_dir):
    result = _invoke(runner, vault_dir, "--json")
    data = json.loads(result.output)
    assert data["total_keys"] == 2


def test_show_json_perfect_score_for_clean_vault(runner, vault_dir):
    result = _invoke(runner, vault_dir, "--json")
    data = json.loads(result.output)
    assert data["score"] == pytest.approx(100.0)
    assert data["grade"] == "A"
