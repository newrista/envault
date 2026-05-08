"""Tests for envault.cooldown."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from envault.cooldown import (
    CooldownActiveError,
    set_cooldown,
    get_cooldown,
    remove_cooldown,
    is_in_cooldown,
    assert_not_in_cooldown,
    list_cooled_keys,
)


@pytest.fixture
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret"}


def test_set_cooldown_stores_entry(secrets):
    set_cooldown(secrets, "API_KEY", 60)
    entry = get_cooldown(secrets, "API_KEY")
    assert entry is not None
    assert entry["duration"] == 60
    assert "locked_at" in entry


def test_get_cooldown_returns_none_when_not_set(secrets):
    assert get_cooldown(secrets, "API_KEY") is None


def test_set_cooldown_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        set_cooldown(secrets, "MISSING", 30)


def test_set_cooldown_internal_key_raises(secrets):
    secrets["__meta__"] = "{}"
    with pytest.raises(KeyError):
        set_cooldown(secrets, "__meta__", 30)


def test_set_cooldown_zero_seconds_raises(secrets):
    with pytest.raises(ValueError):
        set_cooldown(secrets, "API_KEY", 0)


def test_set_cooldown_negative_seconds_raises(secrets):
    with pytest.raises(ValueError):
        set_cooldown(secrets, "API_KEY", -5)


def test_is_in_cooldown_true_when_fresh(secrets):
    set_cooldown(secrets, "API_KEY", 300)
    assert is_in_cooldown(secrets, "API_KEY") is True


def test_is_in_cooldown_false_when_expired(secrets):
    past = datetime.now(timezone.utc) - timedelta(seconds=120)
    with patch("envault.cooldown._now", return_value=past):
        set_cooldown(secrets, "API_KEY", 60)
    assert is_in_cooldown(secrets, "API_KEY") is False


def test_is_in_cooldown_false_when_not_set(secrets):
    assert is_in_cooldown(secrets, "API_KEY") is False


def test_assert_not_in_cooldown_passes_when_no_entry(secrets):
    assert_not_in_cooldown(secrets, "API_KEY")  # should not raise


def test_assert_not_in_cooldown_raises_when_active(secrets):
    set_cooldown(secrets, "API_KEY", 300)
    with pytest.raises(CooldownActiveError) as exc_info:
        assert_not_in_cooldown(secrets, "API_KEY")
    assert exc_info.value.key == "API_KEY"
    assert exc_info.value.remaining_seconds > 0


def test_assert_not_in_cooldown_passes_when_expired(secrets):
    past = datetime.now(timezone.utc) - timedelta(seconds=120)
    with patch("envault.cooldown._now", return_value=past):
        set_cooldown(secrets, "API_KEY", 60)
    assert_not_in_cooldown(secrets, "API_KEY")  # should not raise


def test_remove_cooldown_clears_entry(secrets):
    set_cooldown(secrets, "API_KEY", 60)
    remove_cooldown(secrets, "API_KEY")
    assert get_cooldown(secrets, "API_KEY") is None
    assert is_in_cooldown(secrets, "API_KEY") is False


def test_remove_cooldown_noop_when_missing(secrets):
    remove_cooldown(secrets, "API_KEY")  # should not raise


def test_list_cooled_keys_returns_active_only(secrets):
    past = datetime.now(timezone.utc) - timedelta(seconds=200)
    set_cooldown(secrets, "API_KEY", 300)  # still active
    with patch("envault.cooldown._now", return_value=past):
        set_cooldown(secrets, "DB_PASS", 60)  # will be expired
    result = list_cooled_keys(secrets)
    assert "API_KEY" in result
    assert "DB_PASS" not in result


def test_list_cooled_keys_empty_when_none_set(secrets):
    assert list_cooled_keys(secrets) == []
