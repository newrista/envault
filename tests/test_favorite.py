"""Tests for envault.favorite."""
from __future__ import annotations

import pytest

from envault.favorite import (
    add_favorite,
    remove_favorite,
    is_favorite,
    list_favorites,
)


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret", "TOKEN": "tok"}


def test_add_favorite_marks_key(secrets):
    add_favorite(secrets, "API_KEY")
    assert is_favorite(secrets, "API_KEY")


def test_add_favorite_stores_note(secrets):
    add_favorite(secrets, "API_KEY", note="primary API key")
    favs = list_favorites(secrets)
    entry = next(e for e in favs if e["key"] == "API_KEY")
    assert entry["note"] == "primary API key"


def test_add_favorite_note_stripped(secrets):
    add_favorite(secrets, "DB_PASS", note="  trimmed  ")
    favs = list_favorites(secrets)
    entry = next(e for e in favs if e["key"] == "DB_PASS")
    assert entry["note"] == "trimmed"


def test_add_favorite_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        add_favorite(secrets, "MISSING")


def test_add_favorite_internal_key_raises(secrets):
    secrets["__meta__"] = {}
    with pytest.raises(ValueError, match="internal"):
        add_favorite(secrets, "__meta__")


def test_add_favorite_duplicate_is_idempotent(secrets):
    add_favorite(secrets, "API_KEY", note="first")
    add_favorite(secrets, "API_KEY", note="second")  # overwrites note
    favs = list_favorites(secrets)
    api_entries = [e for e in favs if e["key"] == "API_KEY"]
    assert len(api_entries) == 1
    assert api_entries[0]["note"] == "second"


def test_remove_favorite_unmarks_key(secrets):
    add_favorite(secrets, "TOKEN")
    remove_favorite(secrets, "TOKEN")
    assert not is_favorite(secrets, "TOKEN")


def test_remove_favorite_not_in_favorites_raises(secrets):
    with pytest.raises(KeyError, match="API_KEY"):
        remove_favorite(secrets, "API_KEY")


def test_is_favorite_returns_false_when_not_set(secrets):
    assert not is_favorite(secrets, "DB_PASS")


def test_list_favorites_returns_sorted(secrets):
    add_favorite(secrets, "TOKEN")
    add_favorite(secrets, "API_KEY")
    keys = [e["key"] for e in list_favorites(secrets)]
    assert keys == sorted(keys)


def test_list_favorites_empty_when_none_set(secrets):
    assert list_favorites(secrets) == []


def test_list_favorites_excludes_internal_keys(secrets):
    add_favorite(secrets, "API_KEY")
    keys = [e["key"] for e in list_favorites(secrets)]
    assert all(not k.startswith("__") for k in keys)
