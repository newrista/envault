"""Tests for envault.quota."""

from __future__ import annotations

import pytest
from envault.quota import (
    DEFAULT_MAX_SECRETS,
    DEFAULT_MAX_VALUE_BYTES,
    QuotaExceededError,
    check_quota,
    get_quota,
    quota_status,
    set_quota,
)


@pytest.fixture()
def secrets() -> dict:
    return {"KEY1": "value1", "KEY2": "value2"}


# --- set_quota / get_quota ---

def test_get_quota_returns_defaults_when_not_set(secrets):
    q = get_quota(secrets)
    assert q["max_secrets"] == DEFAULT_MAX_SECRETS
    assert q["max_value_bytes"] == DEFAULT_MAX_VALUE_BYTES


def test_set_quota_persists_max_secrets(secrets):
    set_quota(secrets, max_secrets=10)
    assert get_quota(secrets)["max_secrets"] == 10


def test_set_quota_persists_max_value_bytes(secrets):
    set_quota(secrets, max_value_bytes=256)
    assert get_quota(secrets)["max_value_bytes"] == 256


def test_set_quota_partial_update_preserves_other_field(secrets):
    set_quota(secrets, max_secrets=20, max_value_bytes=512)
    set_quota(secrets, max_secrets=30)
    q = get_quota(secrets)
    assert q["max_secrets"] == 30
    assert q["max_value_bytes"] == 512


def test_set_quota_invalid_max_secrets_raises(secrets):
    with pytest.raises(ValueError, match="max_secrets"):
        set_quota(secrets, max_secrets=0)


def test_set_quota_invalid_max_value_bytes_raises(secrets):
    with pytest.raises(ValueError, match="max_value_bytes"):
        set_quota(secrets, max_value_bytes=-1)


# --- check_quota ---

def test_check_quota_allows_new_key_within_limit(secrets):
    set_quota(secrets, max_secrets=10)
    check_quota(secrets, "NEW_KEY", "val")  # should not raise


def test_check_quota_raises_when_count_exceeded(secrets):
    set_quota(secrets, max_secrets=2)  # already 2 keys
    with pytest.raises(QuotaExceededError, match="count"):
        check_quota(secrets, "NEW_KEY", "val")


def test_check_quota_updating_existing_key_does_not_count_extra(secrets):
    set_quota(secrets, max_secrets=2)  # already 2 keys
    check_quota(secrets, "KEY1", "new_value")  # update, not new — should not raise


def test_check_quota_raises_when_value_too_large(secrets):
    set_quota(secrets, max_value_bytes=5)
    with pytest.raises(QuotaExceededError, match="size"):
        check_quota(secrets, "KEY3", "this_is_too_long")


def test_check_quota_allows_value_at_exact_limit(secrets):
    set_quota(secrets, max_value_bytes=5)
    check_quota(secrets, "KEY3", "hello")  # exactly 5 bytes — should not raise


# --- quota_status ---

def test_quota_status_reports_used_secrets(secrets):
    s = quota_status(secrets)
    assert s["used_secrets"] == 2


def test_quota_status_remaining_decreases_after_set_quota(secrets):
    set_quota(secrets, max_secrets=5)
    s = quota_status(secrets)
    assert s["remaining_secrets"] == 3


def test_quota_status_internal_keys_excluded(secrets):
    secrets["__internal__"] = "meta"
    s = quota_status(secrets)
    assert s["used_secrets"] == 2
