"""Tests for envault CLI hooks commands."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from envault.cli_hooks import hooks_group


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path


def _invoke(runner, vault_dir, *args):
    return runner.invoke(hooks_group, ["--vault-dir", str(vault_dir), *args])


def test_add_hook_succeeds(runner, vault_dir):
    result = _invoke(runner, vault_dir, "add", "post_set", "echo done")
    assert result.exit_code == 0
    assert "Hook registered" in result.output


def test_add_hook_invalid_event_fails(runner, vault_dir):
    result = runner.invoke(hooks_group, ["add", "on_explode", "cmd"])
    assert result.exit_code != 0


def test_remove_hook_succeeds(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "pre_set", "cleanup.sh")
    result = _invoke(runner, vault_dir, "remove", "pre_set", "cleanup.sh")
    assert result.exit_code == 0
    assert "Hook removed" in result.output


def test_remove_nonexistent_hook_fails(runner, vault_dir):
    result = _invoke(runner, vault_dir, "remove", "pre_set", "ghost.sh")
    assert result.exit_code != 0


def test_list_hooks_empty(runner, vault_dir):
    result = _invoke(runner, vault_dir, "list")
    assert result.exit_code == 0
    assert "No hooks registered" in result.output


def test_list_hooks_shows_registered(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "post_rotate", "rotate_notify.sh")
    result = _invoke(runner, vault_dir, "list")
    assert "rotate_notify.sh" in result.output


def test_list_hooks_filtered_by_event(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "post_set", "a.sh")
    _invoke(runner, vault_dir, "add", "pre_delete", "b.sh")
    result = _invoke(runner, vault_dir, "list", "--event", "post_set")
    assert "a.sh" in result.output
    assert "b.sh" not in result.output
