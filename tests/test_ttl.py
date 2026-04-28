"""Tests for envault.ttl module."""

from __future__ import annotations

import time

import pytest

from envault.ttl import (
    _TTL_META_KEY,
    get_ttl,
    is_expired,
    list_expired,
    remove_ttl,
    set_ttl,
)


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "hunter2"}


def test_set_ttl_stores_expiry(secrets):
    set_ttl(secrets, "API_KEY", ttl_seconds=60)
    expiry = get_ttl(secrets, "API_KEY")
    assert expiry is not None
    assert expiry > time.time()
    assert expiry <= time.time() + 61


def test_get_ttl_returns_none_when_not_set(secrets):
    assert get_ttl(secrets, "API_KEY") is None


def test_is_expired_false_for_future_ttl(secrets):
    set_ttl(secrets, "API_KEY", ttl_seconds=3600)
    assert is_expired(secrets, "API_KEY") is False


def test_is_expired_true_for_past_ttl(secrets):
    set_ttl(secrets, "API_KEY", ttl_seconds=0.001)
    time.sleep(0.01)
    assert is_expired(secrets, "API_KEY") is True


def test_is_expired_false_when_no_ttl(secrets):
    assert is_expired(secrets, "DB_PASS") is False


def test_remove_ttl_clears_entry(secrets):
    set_ttl(secrets, "API_KEY", ttl_seconds=60)
    remove_ttl(secrets, "API_KEY")
    assert get_ttl(secrets, "API_KEY") is None


def test_remove_ttl_noop_when_not_set(secrets):
    # Should not raise
    remove_ttl(secrets, "API_KEY")


def test_list_expired_returns_stale_keys(secrets):
    set_ttl(secrets, "API_KEY", ttl_seconds=0.001)
    set_ttl(secrets, "DB_PASS", ttl_seconds=3600)
    time.sleep(0.01)
    expired = list_expired(secrets)
    assert "API_KEY" in expired
    assert "DB_PASS" not in expired


def test_list_expired_empty_when_none_stale(secrets):
    set_ttl(secrets, "API_KEY", ttl_seconds=3600)
    assert list_expired(secrets) == []


def test_set_ttl_raises_for_missing_key(secrets):
    with pytest.raises(KeyError):
        set_ttl(secrets, "NONEXISTENT", ttl_seconds=60)


def test_set_ttl_raises_for_reserved_key(secrets):
    secrets[_TTL_META_KEY] = "{}"
    with pytest.raises(ValueError, match="reserved"):
        set_ttl(secrets, _TTL_META_KEY, ttl_seconds=60)


def test_set_ttl_raises_for_non_positive_seconds(secrets):
    with pytest.raises(ValueError, match="positive"):
        set_ttl(secrets, "API_KEY", ttl_seconds=-10)
