"""Tests for envault.namespace."""

import pytest
from envault.namespace import (
    make_key,
    split_key,
    register_namespace,
    unregister_namespace,
    list_namespaces,
    keys_in_namespace,
    move_to_namespace,
    SEPARATOR,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}


# --- make_key / split_key ---

def test_make_key_joins_with_separator():
    assert make_key("prod", "DB_HOST") == f"prod{SEPARATOR}DB_HOST"


def test_make_key_empty_namespace_raises():
    with pytest.raises(ValueError):
        make_key("", "DB_HOST")


def test_make_key_empty_name_raises():
    with pytest.raises(ValueError):
        make_key("prod", "")


def test_split_key_namespaced():
    ns, name = split_key("prod/DB_HOST")
    assert ns == "prod"
    assert name == "DB_HOST"


def test_split_key_flat_returns_empty_ns():
    ns, name = split_key("DB_HOST")
    assert ns == ""
    assert name == "DB_HOST"


# --- register / unregister ---

def test_register_namespace_creates_entry(secrets):
    register_namespace(secrets, "prod")
    assert "prod" in list_namespaces(secrets)


def test_register_namespace_with_description(secrets):
    register_namespace(secrets, "staging", description="Staging env")
    assert "staging" in list_namespaces(secrets)


def test_register_namespace_is_idempotent(secrets):
    register_namespace(secrets, "prod")
    register_namespace(secrets, "prod")
    assert list_namespaces(secrets).count("prod") == 1


def test_register_empty_namespace_raises(secrets):
    with pytest.raises(ValueError):
        register_namespace(secrets, "")


def test_unregister_namespace_removes_entry(secrets):
    register_namespace(secrets, "prod")
    unregister_namespace(secrets, "prod")
    assert "prod" not in list_namespaces(secrets)


def test_unregister_nonexistent_raises(secrets):
    with pytest.raises(KeyError):
        unregister_namespace(secrets, "ghost")


# --- list_namespaces ---

def test_list_namespaces_empty_initially(secrets):
    assert list_namespaces(secrets) == []


def test_list_namespaces_sorted(secrets):
    register_namespace(secrets, "zebra")
    register_namespace(secrets, "alpha")
    assert list_namespaces(secrets) == ["alpha", "zebra"]


# --- keys_in_namespace ---

def test_keys_in_namespace_returns_matching_keys(secrets):
    secrets["prod/DB_HOST"] = "prod-host"
    secrets["prod/DB_PORT"] = "5432"
    secrets["dev/DB_HOST"] = "dev-host"
    assert keys_in_namespace(secrets, "prod") == ["prod/DB_HOST", "prod/DB_PORT"]


def test_keys_in_namespace_excludes_internal_keys(secrets):
    secrets["prod/SECRET"] = "val"
    secrets["__namespaces__"] = "{}"
    result = keys_in_namespace(secrets, "prod")
    assert "__namespaces__" not in result


def test_keys_in_namespace_empty_when_none_match(secrets):
    assert keys_in_namespace(secrets, "prod") == []


# --- move_to_namespace ---

def test_move_to_namespace_renames_key(secrets):
    new_key = move_to_namespace(secrets, "API_KEY", "prod")
    assert new_key == "prod/API_KEY"
    assert "prod/API_KEY" in secrets
    assert "API_KEY" not in secrets


def test_move_to_namespace_preserves_value(secrets):
    move_to_namespace(secrets, "API_KEY", "prod")
    assert secrets["prod/API_KEY"] == "abc123"


def test_move_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        move_to_namespace(secrets, "MISSING", "prod")


def test_move_clashes_with_existing_raises(secrets):
    secrets["prod/API_KEY"] = "already-here"
    with pytest.raises(ValueError):
        move_to_namespace(secrets, "API_KEY", "prod")
