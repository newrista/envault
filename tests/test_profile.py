"""Tests for envault.profile module."""

from __future__ import annotations

import pytest

from envault.profile import (
    PROFILE_META_KEY,
    create_profile,
    delete_profile,
    add_key_to_profile,
    remove_key_from_profile,
    get_profile_keys,
    list_profiles,
    resolve_profile,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret123", "PORT": "5432"}


def test_create_profile_adds_empty_list(secrets):
    create_profile(secrets, "production")
    assert "production" in secrets[PROFILE_META_KEY]
    assert secrets[PROFILE_META_KEY]["production"] == []


def test_create_profile_is_idempotent(secrets):
    create_profile(secrets, "staging")
    add_key_to_profile(secrets, "staging", "PORT")
    create_profile(secrets, "staging")  # should not overwrite
    assert "PORT" in secrets[PROFILE_META_KEY]["staging"]


def test_delete_profile_removes_entry(secrets):
    create_profile(secrets, "dev")
    delete_profile(secrets, "dev")
    assert "dev" not in secrets.get(PROFILE_META_KEY, {})


def test_delete_nonexistent_profile_raises(secrets):
    with pytest.raises(KeyError, match="ghost"):
        delete_profile(secrets, "ghost")


def test_add_key_to_profile(secrets):
    create_profile(secrets, "prod")
    add_key_to_profile(secrets, "prod", "DB_URL")
    assert "DB_URL" in secrets[PROFILE_META_KEY]["prod"]


def test_add_key_duplicate_is_idempotent(secrets):
    create_profile(secrets, "prod")
    add_key_to_profile(secrets, "prod", "API_KEY")
    add_key_to_profile(secrets, "prod", "API_KEY")
    assert secrets[PROFILE_META_KEY]["prod"].count("API_KEY") == 1


def test_add_key_missing_profile_raises(secrets):
    with pytest.raises(KeyError, match="no_such"):
        add_key_to_profile(secrets, "no_such", "DB_URL")


def test_add_key_missing_secret_raises(secrets):
    create_profile(secrets, "prod")
    with pytest.raises(KeyError, match="MISSING_KEY"):
        add_key_to_profile(secrets, "prod", "MISSING_KEY")


def test_remove_key_from_profile(secrets):
    create_profile(secrets, "prod")
    add_key_to_profile(secrets, "prod", "PORT")
    remove_key_from_profile(secrets, "prod", "PORT")
    assert "PORT" not in secrets[PROFILE_META_KEY]["prod"]


def test_remove_key_not_in_profile_raises(secrets):
    create_profile(secrets, "prod")
    with pytest.raises(KeyError, match="DB_URL"):
        remove_key_from_profile(secrets, "prod", "DB_URL")


def test_get_profile_keys_returns_list(secrets):
    create_profile(secrets, "ci")
    add_key_to_profile(secrets, "ci", "API_KEY")
    add_key_to_profile(secrets, "ci", "PORT")
    keys = get_profile_keys(secrets, "ci")
    assert set(keys) == {"API_KEY", "PORT"}


def test_get_profile_keys_unknown_profile_raises(secrets):
    with pytest.raises(KeyError):
        get_profile_keys(secrets, "unknown")


def test_list_profiles_empty(secrets):
    assert list_profiles(secrets) == []


def test_list_profiles_returns_names(secrets):
    create_profile(secrets, "alpha")
    create_profile(secrets, "beta")
    names = list_profiles(secrets)
    assert set(names) == {"alpha", "beta"}


def test_resolve_profile_returns_values(secrets):
    create_profile(secrets, "prod")
    add_key_to_profile(secrets, "prod", "DB_URL")
    add_key_to_profile(secrets, "prod", "API_KEY")
    resolved = resolve_profile(secrets, "prod")
    assert resolved == {"DB_URL": "postgres://localhost", "API_KEY": "secret123"}


def test_resolve_profile_unknown_raises(secrets):
    with pytest.raises(KeyError):
        resolve_profile(secrets, "nope")
