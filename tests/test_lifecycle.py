"""Tests for envault.lifecycle module."""

from __future__ import annotations

import pytest

from envault.lifecycle import (
    VALID_STATES,
    get_state,
    list_by_state,
    remove_state,
    set_state,
)


@pytest.fixture
def secrets():
    return {"API_KEY": "abc123", "DB_PASS": "secret", "TOKEN": "tok"}


def test_set_state_stores_state(secrets):
    set_state(secrets, "API_KEY", "active")
    entry = get_state(secrets, "API_KEY")
    assert entry["state"] == "active"


def test_set_state_records_timestamps(secrets):
    set_state(secrets, "API_KEY", "active")
    entry = get_state(secrets, "API_KEY")
    assert "created_at" in entry
    assert "updated_at" in entry


def test_set_state_stores_reason(secrets):
    set_state(secrets, "API_KEY", "deprecated", reason="replaced by TOKEN")
    entry = get_state(secrets, "API_KEY")
    assert entry["reason"] == "replaced by TOKEN"


def test_set_state_no_reason_omits_field(secrets):
    set_state(secrets, "API_KEY", "active")
    entry = get_state(secrets, "API_KEY")
    assert "reason" not in entry


def test_set_state_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        set_state(secrets, "MISSING", "active")


def test_set_state_internal_key_raises(secrets):
    secrets["__meta__"] = "{}"
    with pytest.raises(KeyError, match="internal"):
        set_state(secrets, "__meta__", "active")


def test_set_state_invalid_state_raises(secrets):
    with pytest.raises(ValueError, match="Invalid state"):
        set_state(secrets, "API_KEY", "unknown")


def test_set_state_created_at_preserved_on_update(secrets):
    set_state(secrets, "API_KEY", "active")
    first = get_state(secrets, "API_KEY")["created_at"]
    set_state(secrets, "API_KEY", "deprecated")
    second = get_state(secrets, "API_KEY")["created_at"]
    assert first == second


def test_get_state_returns_none_when_not_set(secrets):
    assert get_state(secrets, "API_KEY") is None


def test_list_by_state_returns_matching_keys(secrets):
    set_state(secrets, "API_KEY", "deprecated")
    set_state(secrets, "DB_PASS", "deprecated")
    set_state(secrets, "TOKEN", "active")
    result = list_by_state(secrets, "deprecated")
    assert set(result) == {"API_KEY", "DB_PASS"}


def test_list_by_state_empty_when_none_match(secrets):
    set_state(secrets, "API_KEY", "active")
    result = list_by_state(secrets, "retired")
    assert result == []


def test_list_by_state_invalid_state_raises(secrets):
    with pytest.raises(ValueError, match="Invalid state"):
        list_by_state(secrets, "zombie")


def test_remove_state_deletes_entry(secrets):
    set_state(secrets, "API_KEY", "active")
    remove_state(secrets, "API_KEY")
    assert get_state(secrets, "API_KEY") is None


def test_remove_state_missing_raises(secrets):
    with pytest.raises(KeyError, match="No lifecycle metadata"):
        remove_state(secrets, "API_KEY")


def test_all_valid_states_accepted(secrets):
    for state in VALID_STATES:
        set_state(secrets, "API_KEY", state)
        assert get_state(secrets, "API_KEY")["state"] == state
