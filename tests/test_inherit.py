"""Tests for envault.inherit."""
from __future__ import annotations

import pytest

from envault.inherit import (
    InheritResult,
    get_inherit_chain,
    set_inherit_chain,
    resolve_inherited,
    list_inherited_keys,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def child() -> dict:
    return {"DB_HOST": "localhost", "APP_ENV": "dev"}


@pytest.fixture()
def parent() -> dict:
    return {"DB_HOST": "prod-db", "DB_PORT": "5432", "SECRET_KEY": "s3cr3t"}


@pytest.fixture()
def grandparent() -> dict:
    return {"DB_HOST": "legacy-db", "LEGACY_KEY": "old"}


# ---------------------------------------------------------------------------
# get/set inherit chain
# ---------------------------------------------------------------------------

def test_get_inherit_chain_empty_when_not_set():
    secrets: dict = {}
    assert get_inherit_chain(secrets) == []


def test_set_and_get_inherit_chain_roundtrip():
    secrets: dict = {}
    chain = ["/vaults/base", "/vaults/global"]
    set_inherit_chain(secrets, chain)
    assert get_inherit_chain(secrets) == chain


def test_set_inherit_chain_overwrites_previous():
    secrets: dict = {}
    set_inherit_chain(secrets, ["/a", "/b"])
    set_inherit_chain(secrets, ["/c"])
    assert get_inherit_chain(secrets) == ["/c"]


# ---------------------------------------------------------------------------
# resolve_inherited
# ---------------------------------------------------------------------------

def test_resolve_returns_child_value_when_present(child, parent):
    result = resolve_inherited("DB_HOST", [child, parent])
    assert result.value == "localhost"
    assert result.source_index == 0


def test_resolve_falls_back_to_parent(child, parent):
    result = resolve_inherited("DB_PORT", [child, parent])
    assert result.value == "5432"
    assert result.source_index == 1


def test_resolve_returns_inherit_result_type(child, parent):
    result = resolve_inherited("SECRET_KEY", [child, parent])
    assert isinstance(result, InheritResult)
    assert result.chain_length == 2


def test_resolve_raises_key_error_when_missing(child, parent):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        resolve_inherited("MISSING_KEY", [child, parent])


def test_resolve_raises_value_error_for_internal_key(child, parent):
    with pytest.raises(ValueError, match="internal"):
        resolve_inherited("__meta__", [child, parent])


def test_resolve_three_layer_chain(child, parent, grandparent):
    result = resolve_inherited("LEGACY_KEY", [child, parent, grandparent])
    assert result.value == "old"
    assert result.source_index == 2
    assert result.chain_length == 3


# ---------------------------------------------------------------------------
# list_inherited_keys
# ---------------------------------------------------------------------------

def test_list_inherited_keys_includes_all_unique_keys(child, parent):
    mapping = list_inherited_keys([child, parent])
    assert "DB_HOST" in mapping
    assert "DB_PORT" in mapping
    assert "APP_ENV" in mapping
    assert "SECRET_KEY" in mapping


def test_list_inherited_keys_source_index_is_highest_priority(child, parent):
    mapping = list_inherited_keys([child, parent])
    # DB_HOST exists in both; child (index 0) wins
    assert mapping["DB_HOST"] == 0
    # DB_PORT only in parent (index 1)
    assert mapping["DB_PORT"] == 1


def test_list_inherited_keys_excludes_internal_keys():
    v1 = {"KEY_A": "1", "__internal__": "x"}
    v2 = {"KEY_B": "2"}
    mapping = list_inherited_keys([v1, v2])
    assert "__internal__" not in mapping
    assert "KEY_A" in mapping
    assert "KEY_B" in mapping


def test_list_inherited_keys_empty_vaults():
    assert list_inherited_keys([]) == {}
    assert list_inherited_keys([{}]) == {}
