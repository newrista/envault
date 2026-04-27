"""Tests for envault.diff module."""

from __future__ import annotations

import pytest

from envault.diff import DiffResult, diff_secrets, format_diff


OLD = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "old-key"}
NEW = {"DB_HOST": "prod.db", "DB_PORT": "5432", "SECRET_TOKEN": "tok123"}


def test_diff_detects_added_keys():
    result = diff_secrets(OLD, NEW)
    assert "SECRET_TOKEN" in result.added
    assert "API_KEY" not in result.added


def test_diff_detects_removed_keys():
    result = diff_secrets(OLD, NEW)
    assert "API_KEY" in result.removed
    assert "SECRET_TOKEN" not in result.removed


def test_diff_detects_changed_keys():
    result = diff_secrets(OLD, NEW)
    assert "DB_HOST" in result.changed
    assert "DB_PORT" not in result.changed


def test_diff_detects_unchanged_keys():
    result = diff_secrets(OLD, NEW)
    assert "DB_PORT" in result.unchanged


def test_diff_values_masked_by_default():
    result = diff_secrets(OLD, NEW)
    assert result.added["SECRET_TOKEN"] == "***"
    assert result.removed["API_KEY"] == "***"
    old_val, new_val = result.changed["DB_HOST"]
    assert old_val == "***"
    assert new_val == "***"


def test_diff_show_values_reveals_data():
    result = diff_secrets(OLD, NEW, show_values=True)
    assert result.added["SECRET_TOKEN"] == "tok123"
    assert result.removed["API_KEY"] == "old-key"
    old_val, new_val = result.changed["DB_HOST"]
    assert old_val == "localhost"
    assert new_val == "prod.db"


def test_has_changes_true_when_differences_exist():
    result = diff_secrets(OLD, NEW)
    assert result.has_changes is True


def test_has_changes_false_for_identical_dicts():
    result = diff_secrets(OLD, OLD)
    assert result.has_changes is False


def test_summary_no_changes():
    result = diff_secrets(OLD, OLD)
    assert result.summary() == "No changes detected."


def test_summary_with_changes():
    result = diff_secrets(OLD, NEW)
    summary = result.summary()
    assert "+" in summary or "-" in summary or "~" in summary


def test_format_diff_lines_prefixes():
    result = diff_secrets(OLD, NEW)
    lines = format_diff(result)
    prefixes = {line.strip()[:3] for line in lines}
    assert "[+]" in prefixes or "[-]" in prefixes or "[~]" in prefixes


def test_format_diff_empty_when_no_changes():
    result = diff_secrets(OLD, OLD)
    assert format_diff(result) == []


def test_diff_empty_old():
    result = diff_secrets({}, NEW, show_values=True)
    assert set(result.added.keys()) == set(NEW.keys())
    assert not result.removed
    assert not result.changed


def test_diff_empty_new():
    result = diff_secrets(OLD, {}, show_values=True)
    assert set(result.removed.keys()) == set(OLD.keys())
    assert not result.added
    assert not result.changed
