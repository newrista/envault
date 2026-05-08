"""Tests for envault.rollback."""

from __future__ import annotations

import pytest

from envault.rollback import (
    rollback_to_history,
    rollback_to_checkpoint,
    list_rollback_points,
    RollbackResult,
)
from envault.history import record_history
from envault.checkpoint import create_checkpoint
from envault.readonly import protect


@pytest.fixture()
def secrets() -> dict:
    s: dict = {"API_KEY": "v1", "DB_PASS": "secret"}
    record_history(s, "API_KEY", "v0")
    record_history(s, "API_KEY", "v1")
    return s


def test_rollback_to_history_restores_previous_value(secrets):
    result = rollback_to_history(secrets, "API_KEY", steps=1)
    assert secrets["API_KEY"] == "v1"
    assert "API_KEY" in result.restored


def test_rollback_two_steps(secrets):
    record_history(secrets, "API_KEY", "v2")
    secrets["API_KEY"] = "v2"
    result = rollback_to_history(secrets, "API_KEY", steps=2)
    assert secrets["API_KEY"] == "v0"
    assert result.restored["API_KEY"] == "v0"


def test_rollback_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="not found"):
        rollback_to_history(secrets, "MISSING", steps=1)


def test_rollback_internal_key_raises(secrets):
    secrets["__meta__"] = "x"
    with pytest.raises(KeyError, match="internal"):
        rollback_to_history(secrets, "__meta__", steps=1)


def test_rollback_steps_exceeds_history_raises(secrets):
    with pytest.raises(ValueError, match="Only"):
        rollback_to_history(secrets, "API_KEY", steps=99)


def test_rollback_zero_steps_raises(secrets):
    with pytest.raises(ValueError, match="steps must be"):
        rollback_to_history(secrets, "API_KEY", steps=0)


def test_rollback_protected_key_is_skipped(secrets):
    protect(secrets, "API_KEY")
    result = rollback_to_history(secrets, "API_KEY", steps=1)
    assert "API_KEY" in result.skipped
    assert result.skipped["API_KEY"] == "read-only"
    assert "API_KEY" not in result.restored


def test_rollback_to_checkpoint_restores_all_keys(secrets):
    create_checkpoint(secrets, "cp1")
    secrets["API_KEY"] = "changed"
    secrets["DB_PASS"] = "changed"
    result = rollback_to_checkpoint(secrets, "cp1")
    assert secrets["API_KEY"] == "v1"
    assert secrets["DB_PASS"] == "secret"
    assert len(result.restored) == 2


def test_rollback_to_checkpoint_missing_raises(secrets):
    with pytest.raises(KeyError, match="not found"):
        rollback_to_checkpoint(secrets, "nonexistent")


def test_rollback_to_checkpoint_skips_protected(secrets):
    create_checkpoint(secrets, "cp2")
    secrets["API_KEY"] = "changed"
    protect(secrets, "API_KEY")
    result = rollback_to_checkpoint(secrets, "cp2")
    assert "API_KEY" in result.skipped
    assert secrets["API_KEY"] == "changed"


def test_list_rollback_points_returns_history(secrets):
    points = list_rollback_points(secrets, "API_KEY")
    assert len(points) >= 1
    assert all("value" in p for p in points)


def test_list_rollback_points_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        list_rollback_points(secrets, "NOPE")


def test_rollback_result_repr():
    r = RollbackResult(restored={"K": "v"}, skipped={"X": "read-only"})
    assert "RollbackResult" in repr(r)
