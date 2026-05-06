"""Tests for envault.expiry module."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from envault.expiry import (
    get_expiry,
    is_expired,
    list_expiring,
    remove_expiry,
    set_expiry,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def secrets():
    return {"DB_PASS": "secret", "API_KEY": "abc123", "TOKEN": "xyz"}


def test_set_expiry_stores_future_date(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        expiry = set_expiry(secrets, "DB_PASS", days=30)
    assert expiry == _NOW + timedelta(days=30)
    stored = get_expiry(secrets, "DB_PASS")
    assert stored == _NOW + timedelta(days=30)


def test_set_expiry_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        set_expiry(secrets, "MISSING", days=10)


def test_set_expiry_internal_key_raises(secrets):
    secrets["__meta__"] = "{}"
    with pytest.raises(KeyError):
        set_expiry(secrets, "__meta__", days=5)


def test_set_expiry_zero_days_raises(secrets):
    with pytest.raises(ValueError):
        set_expiry(secrets, "DB_PASS", days=0)


def test_set_expiry_negative_days_raises(secrets):
    with pytest.raises(ValueError):
        set_expiry(secrets, "DB_PASS", days=-1)


def test_get_expiry_returns_none_when_not_set(secrets):
    assert get_expiry(secrets, "DB_PASS") is None


def test_remove_expiry_returns_true_when_removed(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        set_expiry(secrets, "DB_PASS", days=10)
    assert remove_expiry(secrets, "DB_PASS") is True
    assert get_expiry(secrets, "DB_PASS") is None


def test_remove_expiry_returns_false_when_not_set(secrets):
    assert remove_expiry(secrets, "DB_PASS") is False


def test_is_expired_false_for_future_expiry(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        set_expiry(secrets, "API_KEY", days=5)
    future = _NOW + timedelta(days=3)
    with patch("envault.expiry._now", return_value=future):
        assert is_expired(secrets, "API_KEY") is False


def test_is_expired_true_for_past_expiry(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        set_expiry(secrets, "API_KEY", days=5)
    past = _NOW + timedelta(days=10)
    with patch("envault.expiry._now", return_value=past):
        assert is_expired(secrets, "API_KEY") is True


def test_is_expired_false_when_no_expiry_set(secrets):
    assert is_expired(secrets, "TOKEN") is False


def test_list_expiring_returns_keys_within_window(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        set_expiry(secrets, "DB_PASS", days=3)
        set_expiry(secrets, "API_KEY", days=10)
        set_expiry(secrets, "TOKEN", days=6)
    with patch("envault.expiry._now", return_value=_NOW):
        result = list_expiring(secrets, within_days=7)
    keys = [k for k, _ in result]
    assert "DB_PASS" in keys
    assert "TOKEN" in keys
    assert "API_KEY" not in keys


def test_list_expiring_sorted_by_expiry(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        set_expiry(secrets, "TOKEN", days=5)
        set_expiry(secrets, "DB_PASS", days=2)
    with patch("envault.expiry._now", return_value=_NOW):
        result = list_expiring(secrets, within_days=7)
    assert result[0][0] == "DB_PASS"
    assert result[1][0] == "TOKEN"


def test_list_expiring_empty_when_none_due(secrets):
    with patch("envault.expiry._now", return_value=_NOW):
        set_expiry(secrets, "DB_PASS", days=30)
    with patch("envault.expiry._now", return_value=_NOW):
        result = list_expiring(secrets, within_days=7)
    assert result == []
