"""Tests for envault.readonly."""

import pytest

from envault.readonly import (
    ReadOnlyViolationError,
    guard_write,
    is_protected,
    list_protected,
    protect,
    unprotect,
)


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret", "PORT": "5432"}


def test_protect_marks_key_as_readonly(secrets):
    protect(secrets, "API_KEY")
    assert is_protected(secrets, "API_KEY") is True


def test_protect_does_not_affect_other_keys(secrets):
    protect(secrets, "API_KEY")
    assert is_protected(secrets, "DB_PASS") is False


def test_protect_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        protect(secrets, "MISSING")


def test_protect_internal_key_raises(secrets):
    secrets["__meta__"] = {}
    with pytest.raises(KeyError):
        protect(secrets, "__meta__")


def test_unprotect_removes_protection(secrets):
    protect(secrets, "API_KEY")
    unprotect(secrets, "API_KEY")
    assert is_protected(secrets, "API_KEY") is False


def test_unprotect_noop_when_not_protected(secrets):
    # Should not raise even if key was never protected
    unprotect(secrets, "API_KEY")
    assert is_protected(secrets, "API_KEY") is False


def test_list_protected_returns_sorted(secrets):
    protect(secrets, "PORT")
    protect(secrets, "API_KEY")
    assert list_protected(secrets) == ["API_KEY", "PORT"]


def test_list_protected_empty_when_none_set(secrets):
    assert list_protected(secrets) == []


def test_guard_write_raises_for_protected_key(secrets):
    protect(secrets, "DB_PASS")
    with pytest.raises(ReadOnlyViolationError, match="DB_PASS"):
        guard_write(secrets, "DB_PASS")


def test_guard_write_passes_for_unprotected_key(secrets):
    # Should not raise
    guard_write(secrets, "DB_PASS")


def test_protect_multiple_keys_independently(secrets):
    protect(secrets, "API_KEY")
    protect(secrets, "DB_PASS")
    assert list_protected(secrets) == ["API_KEY", "DB_PASS"]
    unprotect(secrets, "API_KEY")
    assert list_protected(secrets) == ["DB_PASS"]


def test_is_protected_false_for_unknown_key(secrets):
    assert is_protected(secrets, "NONEXISTENT") is False
