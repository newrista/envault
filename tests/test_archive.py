"""Tests for envault.archive."""

import pytest
from envault.archive import (
    archive_secret,
    restore_secret,
    get_archived,
    list_archived,
    purge_archived,
    ARCHIVED_KEY,
)


@pytest.fixture
def secrets():
    return {"API_KEY": "abc123", "DB_PASS": "secret", "TOKEN": "tok"}


def test_archive_removes_key_from_active(secrets):
    archive_secret(secrets, "API_KEY")
    assert "API_KEY" not in secrets


def test_archive_stores_value_in_index(secrets):
    archive_secret(secrets, "API_KEY")
    meta = get_archived(secrets, "API_KEY")
    assert meta is not None
    assert meta["value"] == "abc123"


def test_archive_stores_reason(secrets):
    archive_secret(secrets, "API_KEY", reason="deprecated")
    meta = get_archived(secrets, "API_KEY")
    assert meta["reason"] == "deprecated"


def test_archive_empty_reason_by_default(secrets):
    archive_secret(secrets, "API_KEY")
    meta = get_archived(secrets, "API_KEY")
    assert meta["reason"] == ""


def test_archive_records_timestamp(secrets):
    archive_secret(secrets, "API_KEY")
    meta = get_archived(secrets, "API_KEY")
    assert "archived_at" in meta
    assert meta["archived_at"].startswith("20")


def test_archive_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        archive_secret(secrets, "MISSING")


def test_archive_internal_key_raises(secrets):
    secrets["__meta__"] = {}
    with pytest.raises(KeyError, match="internal"):
        archive_secret(secrets, "__meta__")


def test_list_archived_returns_keys(secrets):
    archive_secret(secrets, "API_KEY")
    archive_secret(secrets, "TOKEN")
    archived = list_archived(secrets)
    assert set(archived) == {"API_KEY", "TOKEN"}


def test_list_archived_empty_when_none(secrets):
    assert list_archived(secrets) == []


def test_restore_brings_key_back(secrets):
    archive_secret(secrets, "DB_PASS")
    restore_secret(secrets, "DB_PASS")
    assert secrets["DB_PASS"] == "secret"


def test_restore_removes_from_archive_index(secrets):
    archive_secret(secrets, "DB_PASS")
    restore_secret(secrets, "DB_PASS")
    assert get_archived(secrets, "DB_PASS") is None


def test_restore_missing_archived_key_raises(secrets):
    with pytest.raises(KeyError, match="NOT_THERE"):
        restore_secret(secrets, "NOT_THERE")


def test_purge_removes_from_archive(secrets):
    archive_secret(secrets, "TOKEN")
    purge_archived(secrets, "TOKEN")
    assert get_archived(secrets, "TOKEN") is None
    assert "TOKEN" not in list_archived(secrets)


def test_purge_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="GHOST"):
        purge_archived(secrets, "GHOST")


def test_archive_does_not_affect_other_keys(secrets):
    archive_secret(secrets, "API_KEY")
    assert secrets["DB_PASS"] == "secret"
    assert secrets["TOKEN"] == "tok"
