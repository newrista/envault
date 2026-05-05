"""Tests for envault.merge."""

from __future__ import annotations

import pytest

from envault.merge import ConflictStrategy, MergeResult, merge_secrets


@pytest.fixture()
def src() -> dict:
    return {"API_KEY": "new_key", "DB_URL": "postgres://new", "ONLY_IN_SRC": "hello"}


@pytest.fixture()
def dst() -> dict:
    return {"API_KEY": "old_key", "SECRET": "existing"}


# ---------------------------------------------------------------------------
# Basic merging
# ---------------------------------------------------------------------------

def test_merge_adds_new_keys(src, dst):
    result = merge_secrets(src, dst)
    assert "ONLY_IN_SRC" in dst
    assert dst["ONLY_IN_SRC"] == "hello"
    assert "ONLY_IN_SRC" in result.added


def test_merge_keep_strategy_preserves_existing(src, dst):
    merge_secrets(src, dst, strategy=ConflictStrategy.KEEP)
    assert dst["API_KEY"] == "old_key"  # unchanged
    assert "API_KEY" in merge_secrets(src, dict(dst), strategy=ConflictStrategy.KEEP).skipped


def test_merge_overwrite_strategy_replaces_existing(src, dst):
    result = merge_secrets(src, dst, strategy=ConflictStrategy.OVERWRITE)
    assert dst["API_KEY"] == "new_key"
    assert "API_KEY" in result.overwritten


def test_merge_skip_strategy_same_as_keep_for_conflicts(src, dst):
    result = merge_secrets(src, dst, strategy=ConflictStrategy.SKIP)
    assert dst["API_KEY"] == "old_key"
    assert "API_KEY" in result.skipped


# ---------------------------------------------------------------------------
# Key filtering
# ---------------------------------------------------------------------------

def test_merge_explicit_keys_limits_scope(src, dst):
    result = merge_secrets(src, dst, keys=["ONLY_IN_SRC"])
    assert "ONLY_IN_SRC" in dst
    assert "DB_URL" not in dst
    assert result.added == ["ONLY_IN_SRC"]


def test_merge_explicit_key_not_in_src_reports_error(dst):
    result = merge_secrets({}, dst, keys=["MISSING"])
    assert any("MISSING" in e for e in result.errors)


def test_merge_prefix_filter(src, dst):
    src["DB_PASS"] = "s3cr3t"
    result = merge_secrets(src, dst, prefix="DB_")
    assert "DB_URL" in dst
    assert "DB_PASS" in dst
    assert "ONLY_IN_SRC" not in dst
    assert "API_KEY" not in result.added


# ---------------------------------------------------------------------------
# Internal key protection
# ---------------------------------------------------------------------------

def test_merge_skips_internal_keys_automatically():
    src = {"__rotation_meta": "x", "REAL_KEY": "val"}
    dst = {}
    result = merge_secrets(src, dst)
    assert "__rotation_meta" not in dst
    assert "REAL_KEY" in dst


def test_merge_explicit_internal_key_reports_error(dst):
    src = {"__rotation_meta": "x"}
    result = merge_secrets(src, dst, keys=["__rotation_meta"])
    assert any("__rotation_meta" in e for e in result.errors)
    assert "__rotation_meta" not in dst


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

def test_merge_returns_merge_result_namedtuple(src, dst):
    result = merge_secrets(src, dst)
    assert isinstance(result, MergeResult)
    assert isinstance(result.added, list)
    assert isinstance(result.skipped, list)
    assert isinstance(result.overwritten, list)
    assert isinstance(result.errors, list)


def test_merge_empty_src_produces_no_changes(dst):
    original = dict(dst)
    result = merge_secrets({}, dst)
    assert dst == original
    assert result.added == []
    assert result.overwritten == []
