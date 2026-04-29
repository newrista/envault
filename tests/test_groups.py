"""Tests for envault.groups."""

from __future__ import annotations

import pytest

from envault.groups import (
    _GROUPS_KEY,
    add_to_group,
    create_group,
    delete_group,
    get_group_keys,
    list_groups,
    remove_from_group,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123", "TOKEN": "tok"}


def test_create_group_adds_empty_list(secrets):
    create_group(secrets, "database")
    assert "database" in secrets[_GROUPS_KEY]
    assert secrets[_GROUPS_KEY]["database"] == []


def test_create_group_is_idempotent(secrets):
    create_group(secrets, "database")
    create_group(secrets, "database")
    assert secrets[_GROUPS_KEY]["database"] == []


def test_delete_group_removes_entry(secrets):
    create_group(secrets, "database")
    delete_group(secrets, "database")
    assert "database" not in secrets.get(_GROUPS_KEY, {})


def test_delete_nonexistent_group_raises(secrets):
    with pytest.raises(KeyError, match="does not exist"):
        delete_group(secrets, "ghost")


def test_add_to_group_appends_key(secrets):
    create_group(secrets, "infra")
    add_to_group(secrets, "infra", "DB_URL")
    assert "DB_URL" in secrets[_GROUPS_KEY]["infra"]


def test_add_to_group_is_idempotent(secrets):
    create_group(secrets, "infra")
    add_to_group(secrets, "infra", "DB_URL")
    add_to_group(secrets, "infra", "DB_URL")
    assert secrets[_GROUPS_KEY]["infra"].count("DB_URL") == 1


def test_add_missing_key_raises(secrets):
    create_group(secrets, "infra")
    with pytest.raises(KeyError, match="does not exist in the vault"):
        add_to_group(secrets, "infra", "MISSING")


def test_add_to_missing_group_raises(secrets):
    with pytest.raises(KeyError, match="does not exist"):
        add_to_group(secrets, "ghost", "DB_URL")


def test_remove_from_group(secrets):
    create_group(secrets, "infra")
    add_to_group(secrets, "infra", "DB_URL")
    remove_from_group(secrets, "infra", "DB_URL")
    assert "DB_URL" not in secrets[_GROUPS_KEY]["infra"]


def test_remove_key_not_in_group_raises(secrets):
    create_group(secrets, "infra")
    with pytest.raises(KeyError, match="not in group"):
        remove_from_group(secrets, "infra", "DB_URL")


def test_get_group_keys_returns_list(secrets):
    create_group(secrets, "web")
    add_to_group(secrets, "web", "API_KEY")
    add_to_group(secrets, "web", "TOKEN")
    assert set(get_group_keys(secrets, "web")) == {"API_KEY", "TOKEN"}


def test_get_group_keys_nonexistent_raises(secrets):
    with pytest.raises(KeyError, match="does not exist"):
        get_group_keys(secrets, "nope")


def test_list_groups_returns_all(secrets):
    create_group(secrets, "alpha")
    create_group(secrets, "beta")
    groups = list_groups(secrets)
    assert "alpha" in groups
    assert "beta" in groups


def test_list_groups_empty_when_none(secrets):
    assert list_groups(secrets) == []
