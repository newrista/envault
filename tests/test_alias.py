"""Tests for envault.alias."""

from __future__ import annotations

import pytest

from envault.alias import (
    add_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
    get_via_alias,
    ALIAS_INDEX_KEY,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret123"}


def test_add_alias_creates_mapping(secrets):
    add_alias(secrets, "database_host", "DB_HOST")
    assert list_aliases(secrets)["database_host"] == "DB_HOST"


def test_add_alias_multiple(secrets):
    add_alias(secrets, "host", "DB_HOST")
    add_alias(secrets, "port", "DB_PORT")
    aliases = list_aliases(secrets)
    assert aliases["host"] == "DB_HOST"
    assert aliases["port"] == "DB_PORT"


def test_add_alias_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        add_alias(secrets, "x", "MISSING")


def test_add_alias_clashes_with_real_key_raises(secrets):
    with pytest.raises(ValueError, match="DB_HOST"):
        add_alias(secrets, "DB_HOST", "API_KEY")


def test_add_alias_reserved_key_raises(secrets):
    with pytest.raises(ValueError, match="reserved"):
        add_alias(secrets, ALIAS_INDEX_KEY, "DB_HOST")


def test_remove_alias(secrets):
    add_alias(secrets, "host", "DB_HOST")
    remove_alias(secrets, "host")
    assert "host" not in list_aliases(secrets)


def test_remove_alias_not_found_raises(secrets):
    with pytest.raises(KeyError, match="nonexistent"):
        remove_alias(secrets, "nonexistent")


def test_resolve_alias_returns_canonical(secrets):
    add_alias(secrets, "host", "DB_HOST")
    assert resolve_alias(secrets, "host") == "DB_HOST"


def test_resolve_alias_returns_none_for_unknown(secrets):
    assert resolve_alias(secrets, "unknown") is None


def test_list_aliases_empty_initially(secrets):
    assert list_aliases(secrets) == {}


def test_get_via_alias_using_alias(secrets):
    add_alias(secrets, "host", "DB_HOST")
    assert get_via_alias(secrets, "host") == "localhost"


def test_get_via_alias_using_real_key(secrets):
    assert get_via_alias(secrets, "DB_HOST") == "localhost"


def test_get_via_alias_missing_raises(secrets):
    with pytest.raises(KeyError):
        get_via_alias(secrets, "NONEXISTENT")
