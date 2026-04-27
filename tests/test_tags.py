"""Tests for envault.tags module."""

from __future__ import annotations

import pytest

from envault.tags import (
    add_tag,
    remove_tag,
    get_tags,
    list_by_tag,
    all_tags,
    _TAGS_KEY,
)


@pytest.fixture()
def secrets() -> dict:
    return {"DB_URL": "postgres://localhost", "API_KEY": "secret123"}


def test_add_tag_attaches_tag(secrets):
    add_tag(secrets, "DB_URL", "database")
    assert "database" in get_tags(secrets, "DB_URL")


def test_add_tag_multiple_tags(secrets):
    add_tag(secrets, "API_KEY", "auth")
    add_tag(secrets, "API_KEY", "external")
    tags = get_tags(secrets, "API_KEY")
    assert "auth" in tags
    assert "external" in tags


def test_add_tag_duplicate_is_idempotent(secrets):
    add_tag(secrets, "DB_URL", "database")
    add_tag(secrets, "DB_URL", "database")
    assert get_tags(secrets, "DB_URL").count("database") == 1


def test_add_tag_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        add_tag(secrets, "MISSING", "sometag")


def test_add_tag_reserved_key_raises(secrets):
    secrets[_TAGS_KEY] = "{}"
    with pytest.raises(KeyError):
        add_tag(secrets, _TAGS_KEY, "meta")


def test_remove_tag_removes_existing(secrets):
    add_tag(secrets, "DB_URL", "database")
    remove_tag(secrets, "DB_URL", "database")
    assert "database" not in get_tags(secrets, "DB_URL")


def test_remove_tag_missing_tag_is_silent(secrets):
    remove_tag(secrets, "DB_URL", "nonexistent")
    assert get_tags(secrets, "DB_URL") == []


def test_get_tags_returns_empty_list_for_untagged(secrets):
    assert get_tags(secrets, "DB_URL") == []


def test_list_by_tag_returns_matching_keys(secrets):
    add_tag(secrets, "DB_URL", "infra")
    add_tag(secrets, "API_KEY", "infra")
    result = list_by_tag(secrets, "infra")
    assert set(result) == {"DB_URL", "API_KEY"}


def test_list_by_tag_no_match_returns_empty(secrets):
    assert list_by_tag(secrets, "ghost") == []


def test_all_tags_returns_full_index(secrets):
    add_tag(secrets, "DB_URL", "database")
    add_tag(secrets, "API_KEY", "auth")
    index = all_tags(secrets)
    assert "DB_URL" in index
    assert "API_KEY" in index


def test_all_tags_empty_when_no_tags(secrets):
    assert all_tags(secrets) == {}
