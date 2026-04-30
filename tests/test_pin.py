"""Tests for envault.pin."""

from __future__ import annotations

import pytest

from envault.pin import (
    pin_secret,
    unpin_secret,
    is_pinned,
    get_pin_reason,
    list_pinned,
)


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret"}


def test_pin_secret_marks_key_as_pinned(secrets):
    pin_secret(secrets, "API_KEY")
    assert is_pinned(secrets, "API_KEY")


def test_pin_secret_stores_reason(secrets):
    pin_secret(secrets, "API_KEY", reason="stable prod key")
    assert get_pin_reason(secrets, "API_KEY") == "stable prod key"


def test_pin_secret_empty_reason_by_default(secrets):
    pin_secret(secrets, "API_KEY")
    assert get_pin_reason(secrets, "API_KEY") == ""


def test_pin_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        pin_secret(secrets, "MISSING")


def test_pin_internal_key_raises(secrets):
    secrets["__meta__"] = {}
    with pytest.raises(KeyError):
        pin_secret(secrets, "__meta__")


def test_unpin_removes_pin(secrets):
    pin_secret(secrets, "API_KEY")
    unpin_secret(secrets, "API_KEY")
    assert not is_pinned(secrets, "API_KEY")


def test_unpin_not_pinned_raises(secrets):
    with pytest.raises(KeyError, match="not pinned"):
        unpin_secret(secrets, "API_KEY")


def test_is_pinned_false_before_pinning(secrets):
    assert not is_pinned(secrets, "DB_PASS")


def test_get_pin_reason_none_when_not_pinned(secrets):
    assert get_pin_reason(secrets, "API_KEY") is None


def test_list_pinned_empty_initially(secrets):
    assert list_pinned(secrets) == {}


def test_list_pinned_returns_all_pinned(secrets):
    pin_secret(secrets, "API_KEY", reason="r1")
    pin_secret(secrets, "DB_PASS", reason="r2")
    result = list_pinned(secrets)
    assert result == {"API_KEY": "r1", "DB_PASS": "r2"}


def test_pin_is_idempotent(secrets):
    pin_secret(secrets, "API_KEY", reason="first")
    pin_secret(secrets, "API_KEY", reason="updated")
    assert get_pin_reason(secrets, "API_KEY") == "updated"
    assert len(list_pinned(secrets)) == 1
