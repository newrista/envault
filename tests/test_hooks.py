"""Tests for envault.hooks lifecycle hook management."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from envault.hooks import (
    register_hook,
    unregister_hook,
    list_hooks,
    fire_hook,
    HOOK_EVENTS,
)


@pytest.fixture
def vault_dir(tmp_path):
    return tmp_path


def test_register_hook_creates_entry(vault_dir):
    register_hook(vault_dir, "post_set", "echo hello")
    hooks = list_hooks(vault_dir)
    assert "echo hello" in hooks["post_set"]


def test_register_hook_invalid_event_raises(vault_dir):
    with pytest.raises(ValueError, match="Unknown event"):
        register_hook(vault_dir, "on_explode", "rm -rf /")


def test_register_hook_is_idempotent(vault_dir):
    register_hook(vault_dir, "pre_set", "echo hi")
    register_hook(vault_dir, "pre_set", "echo hi")
    hooks = list_hooks(vault_dir)
    assert hooks["pre_set"].count("echo hi") == 1


def test_register_multiple_hooks_same_event(vault_dir):
    register_hook(vault_dir, "post_rotate", "cmd1")
    register_hook(vault_dir, "post_rotate", "cmd2")
    hooks = list_hooks(vault_dir)
    assert "cmd1" in hooks["post_rotate"]
    assert "cmd2" in hooks["post_rotate"]


def test_unregister_hook_removes_entry(vault_dir):
    register_hook(vault_dir, "pre_delete", "notify.sh")
    unregister_hook(vault_dir, "pre_delete", "notify.sh")
    hooks = list_hooks(vault_dir)
    assert "notify.sh" not in hooks["pre_delete"]


def test_unregister_nonexistent_hook_raises(vault_dir):
    with pytest.raises(KeyError):
        unregister_hook(vault_dir, "pre_set", "ghost.sh")


def test_unregister_invalid_event_raises(vault_dir):
    with pytest.raises(ValueError):
        unregister_hook(vault_dir, "bad_event", "cmd")


def test_list_hooks_filtered_by_event(vault_dir):
    register_hook(vault_dir, "post_set", "a.sh")
    register_hook(vault_dir, "pre_set", "b.sh")
    result = list_hooks(vault_dir, event="post_set")
    assert "post_set" in result
    assert "pre_set" not in result


def test_list_hooks_invalid_event_raises(vault_dir):
    with pytest.raises(ValueError):
        list_hooks(vault_dir, event="nope")


def test_list_hooks_empty_when_no_file(vault_dir):
    hooks = list_hooks(vault_dir)
    assert all(hooks[e] == [] for e in HOOK_EVENTS)


def test_fire_hook_runs_commands(vault_dir):
    register_hook(vault_dir, "post_set", "echo fired")
    with patch("subprocess.run") as mock_run:
        fired = fire_hook(vault_dir, "post_set", context={"KEY": "MY_VAR"})
    assert "echo fired" in fired
    mock_run.assert_called_once()


def test_fire_hook_returns_empty_when_no_hooks(vault_dir):
    with patch("subprocess.run") as mock_run:
        fired = fire_hook(vault_dir, "pre_rotate")
    assert fired == []
    mock_run.assert_not_called()


def test_fire_hook_invalid_event_raises(vault_dir):
    with pytest.raises(ValueError):
        fire_hook(vault_dir, "on_fire")
