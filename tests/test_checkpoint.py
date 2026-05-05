"""Tests for envault.checkpoint."""

from __future__ import annotations

import time
import pytest

from envault.checkpoint import (
    CHECKPOINT_KEY,
    create_checkpoint,
    delete_checkpoint,
    get_checkpoint,
    list_checkpoints,
    diff_from_checkpoint,
)


@pytest.fixture
def secrets():
    return {"DB_URL": "postgres://", "API_KEY": "abc123", "PORT": "5432"}


def test_create_checkpoint_stores_metadata(secrets):
    meta = create_checkpoint(secrets, "v1", "initial")
    assert "created_at" in meta
    assert meta["description"] == "initial"
    assert set(meta["keys"]) == {"DB_URL", "API_KEY", "PORT"}


def test_create_checkpoint_persists_in_secrets(secrets):
    create_checkpoint(secrets, "v1")
    assert CHECKPOINT_KEY in secrets
    assert "v1" in secrets[CHECKPOINT_KEY]


def test_create_checkpoint_invalid_name_raises(secrets):
    with pytest.raises(ValueError, match="Invalid checkpoint name"):
        create_checkpoint(secrets, "bad-name!")


def test_create_checkpoint_excludes_internal_keys(secrets):
    secrets["__meta__"] = "internal"
    meta = create_checkpoint(secrets, "snap")
    assert "__meta__" not in meta["keys"]


def test_get_checkpoint_returns_metadata(secrets):
    create_checkpoint(secrets, "v1", "desc")
    cp = get_checkpoint(secrets, "v1")
    assert cp["description"] == "desc"


def test_get_checkpoint_missing_raises(secrets):
    with pytest.raises(KeyError, match="does not exist"):
        get_checkpoint(secrets, "ghost")


def test_delete_checkpoint_removes_entry(secrets):
    create_checkpoint(secrets, "v1")
    delete_checkpoint(secrets, "v1")
    with pytest.raises(KeyError):
        get_checkpoint(secrets, "v1")


def test_delete_checkpoint_missing_raises(secrets):
    with pytest.raises(KeyError, match="does not exist"):
        delete_checkpoint(secrets, "nope")


def test_list_checkpoints_empty(secrets):
    assert list_checkpoints(secrets) == []


def test_list_checkpoints_sorted_by_time(secrets):
    create_checkpoint(secrets, "first")
    time.sleep(0.01)
    create_checkpoint(secrets, "second")
    names = [c["name"] for c in list_checkpoints(secrets)]
    assert names == ["first", "second"]


def test_diff_from_checkpoint_detects_added_key(secrets):
    create_checkpoint(secrets, "snap")
    secrets["NEW_KEY"] = "value"
    result = diff_from_checkpoint(secrets, "snap")
    assert "NEW_KEY" in result["added"]
    assert result["removed"] == []


def test_diff_from_checkpoint_detects_removed_key(secrets):
    create_checkpoint(secrets, "snap")
    del secrets["PORT"]
    result = diff_from_checkpoint(secrets, "snap")
    assert "PORT" in result["removed"]
    assert result["added"] == []


def test_diff_from_checkpoint_no_changes(secrets):
    create_checkpoint(secrets, "snap")
    result = diff_from_checkpoint(secrets, "snap")
    assert result == {"added": [], "removed": []}
