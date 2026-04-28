"""Tests for envault.access module."""

from __future__ import annotations

import pytest
from envault.access import (
    ACCESS_META_KEY,
    PERM_DENY,
    PERM_READ,
    PERM_WRITE,
    check_access,
    get_permission,
    list_permissions,
    remove_permission,
    set_permission,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}


def test_set_permission_stores_rule(secrets):
    set_permission(secrets, "DB_URL", [PERM_READ])
    rules = list_permissions(secrets)
    assert "DB_URL" in rules
    assert PERM_READ in rules["DB_URL"]


def test_set_permission_invalid_perm_raises(secrets):
    with pytest.raises(ValueError, match="Unknown permission"):
        set_permission(secrets, "DB_URL", ["execute"])


def test_get_permission_exact_match(secrets):
    set_permission(secrets, "API_KEY", [PERM_READ])
    perms = get_permission(secrets, "API_KEY")
    assert PERM_READ in perms
    assert PERM_WRITE not in perms


def test_get_permission_glob_pattern(secrets):
    set_permission(secrets, "DB_*", [PERM_READ])
    perms = get_permission(secrets, "DB_URL")
    assert PERM_READ in perms


def test_get_permission_default_is_full_access(secrets):
    perms = get_permission(secrets, "SOME_KEY")
    assert PERM_READ in perms
    assert PERM_WRITE in perms


def test_remove_permission_returns_true_when_exists(secrets):
    set_permission(secrets, "API_KEY", [PERM_READ])
    result = remove_permission(secrets, "API_KEY")
    assert result is True
    assert "API_KEY" not in list_permissions(secrets)


def test_remove_permission_returns_false_when_missing(secrets):
    result = remove_permission(secrets, "NONEXISTENT")
    assert result is False


def test_check_access_granted(secrets):
    set_permission(secrets, "DB_URL", [PERM_READ, PERM_WRITE])
    assert check_access(secrets, "DB_URL", PERM_READ) is True
    assert check_access(secrets, "DB_URL", PERM_WRITE) is True


def test_check_access_denied_by_deny_perm(secrets):
    set_permission(secrets, "API_KEY", [PERM_DENY])
    assert check_access(secrets, "API_KEY", PERM_READ) is False
    assert check_access(secrets, "API_KEY", PERM_WRITE) is False


def test_check_access_missing_perm(secrets):
    set_permission(secrets, "DB_URL", [PERM_READ])
    assert check_access(secrets, "DB_URL", PERM_WRITE) is False


def test_list_permissions_empty_initially(secrets):
    assert list_permissions(secrets) == {}


def test_meta_key_not_overwritten_by_accident(secrets):
    set_permission(secrets, "X", [PERM_READ])
    assert ACCESS_META_KEY in secrets
    # Ensure the meta key itself is not treated as a user secret
    rules = list_permissions(secrets)
    assert ACCESS_META_KEY not in rules
