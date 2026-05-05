"""Tests for envault.history."""

from __future__ import annotations

import pytest

from envault.history import (
    record_history,
    get_history,
    clear_history,
    list_keys_with_history,
    MAX_HISTORY,
    _HISTORY_KEY,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_URL": "postgres://localhost/dev", "API_KEY": "abc123"}


def test_record_history_appends_entry(secrets):
    record_history(secrets, "DB_URL", "postgres://old/db")
    entries = get_history(secrets, "DB_URL")
    assert len(entries) == 1
    assert entries[0]["value"] == "postgres://old/db"


def test_record_history_stores_timestamp(secrets):
    record_history(secrets, "API_KEY", "old_key")
    entry = get_history(secrets, "API_KEY")[0]
    assert "recorded_at" in entry
    assert entry["recorded_at"].endswith("+00:00")


def test_record_multiple_entries_ordered(secrets):
    for val in ["v1", "v2", "v3"]:
        record_history(secrets, "API_KEY", val)
    entries = get_history(secrets, "API_KEY")
    assert [e["value"] for e in entries] == ["v1", "v2", "v3"]


def test_history_capped_at_max(secrets):
    for i in range(MAX_HISTORY + 5):
        record_history(secrets, "DB_URL", f"value_{i}")
    entries = get_history(secrets, "DB_URL")
    assert len(entries) == MAX_HISTORY
    # Oldest entries should have been dropped
    assert entries[0]["value"] == "value_5"


def test_get_history_returns_empty_for_key_with_no_history(secrets):
    assert get_history(secrets, "DB_URL") == []


def test_get_history_raises_for_missing_key(secrets):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        get_history(secrets, "MISSING_KEY")


def test_clear_history_removes_entries(secrets):
    record_history(secrets, "API_KEY", "old")
    clear_history(secrets, "API_KEY")
    assert get_history(secrets, "API_KEY") == []


def test_clear_history_raises_for_missing_key(secrets):
    with pytest.raises(KeyError):
        clear_history(secrets, "NOT_THERE")


def test_list_keys_with_history_returns_recorded_keys(secrets):
    record_history(secrets, "DB_URL", "old_url")
    record_history(secrets, "API_KEY", "old_key")
    keys = list_keys_with_history(secrets)
    assert set(keys) == {"DB_URL", "API_KEY"}


def test_list_keys_with_history_empty_when_no_history(secrets):
    assert list_keys_with_history(secrets) == []


def test_internal_key_not_recorded(secrets):
    """Keys starting with __ should be silently ignored."""
    record_history(secrets, "__meta__", "ignored")
    assert _HISTORY_KEY not in get_history.__module__  # sanity
    index = secrets.get(_HISTORY_KEY, {})
    assert "__meta__" not in index
