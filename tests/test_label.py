"""Tests for envault.label."""

from __future__ import annotations

import pytest

from envault.label import (
    _LABELS_KEY,
    get_label,
    list_labels,
    remove_label,
    set_label,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}


def test_set_label_attaches_label(secrets):
    set_label(secrets, "DB_URL", "Database URL")
    assert secrets[_LABELS_KEY]["DB_URL"] == "Database URL"


def test_set_label_multiple_keys(secrets):
    set_label(secrets, "DB_URL", "Database URL")
    set_label(secrets, "API_KEY", "API Key")
    assert secrets[_LABELS_KEY]["DB_URL"] == "Database URL"
    assert secrets[_LABELS_KEY]["API_KEY"] == "API Key"


def test_set_label_overwrites_existing(secrets):
    set_label(secrets, "DB_URL", "Old Label")
    set_label(secrets, "DB_URL", "New Label")
    assert secrets[_LABELS_KEY]["DB_URL"] == "New Label"


def test_set_label_strips_whitespace(secrets):
    set_label(secrets, "DB_URL", "  Trimmed  ")
    assert secrets[_LABELS_KEY]["DB_URL"] == "Trimmed"


def test_set_label_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        set_label(secrets, "MISSING", "Some Label")


def test_set_label_empty_label_raises(secrets):
    with pytest.raises(ValueError, match="empty"):
        set_label(secrets, "DB_URL", "   ")


def test_set_label_internal_key_raises(secrets):
    secrets["__meta__"] = {}
    with pytest.raises(KeyError, match="internal"):
        set_label(secrets, "__meta__", "Meta")


def test_get_label_returns_value(secrets):
    set_label(secrets, "API_KEY", "API Key")
    assert get_label(secrets, "API_KEY") == "API Key"


def test_get_label_returns_none_when_not_set(secrets):
    assert get_label(secrets, "DB_URL") is None


def test_remove_label_clears_entry(secrets):
    set_label(secrets, "DB_URL", "Database URL")
    remove_label(secrets, "DB_URL")
    assert get_label(secrets, "DB_URL") is None


def test_remove_label_noop_when_not_set(secrets):
    # Should not raise even if no label was set.
    remove_label(secrets, "DB_URL")
    assert get_label(secrets, "DB_URL") is None


def test_remove_label_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        remove_label(secrets, "MISSING")


def test_list_labels_returns_all(secrets):
    set_label(secrets, "DB_URL", "Database URL")
    set_label(secrets, "API_KEY", "API Key")
    result = list_labels(secrets)
    assert result == {"DB_URL": "Database URL", "API_KEY": "API Key"}


def test_list_labels_empty_when_none_set(secrets):
    assert list_labels(secrets) == {}


def test_list_labels_returns_copy(secrets):
    set_label(secrets, "DB_URL", "Database URL")
    result = list_labels(secrets)
    result["DB_URL"] = "Mutated"
    assert get_label(secrets, "DB_URL") == "Database URL"
