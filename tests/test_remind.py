"""Tests for envault.remind."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from envault.remind import expiring_soon, rotation_overdue, reminder_report
from envault.ttl import set_ttl
from envault.rotation import set_rotation_metadata


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret", "TOKEN": "tok"}


def _future(seconds: int) -> datetime:
    return datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)


def _past(seconds: int) -> datetime:
    return datetime.now(tz=timezone.utc) - timedelta(seconds=seconds)


# --- expiring_soon ---

def test_expiring_soon_returns_key_within_window(secrets):
    set_ttl(secrets, "API_KEY", _future(3600))
    result = expiring_soon(secrets, within_seconds=86400)
    keys = [r["key"] for r in result]
    assert "API_KEY" in keys


def test_expiring_soon_excludes_key_outside_window(secrets):
    set_ttl(secrets, "API_KEY", _future(90000))
    result = expiring_soon(secrets, within_seconds=86400)
    keys = [r["key"] for r in result]
    assert "API_KEY" not in keys


def test_expiring_soon_excludes_already_expired(secrets):
    set_ttl(secrets, "API_KEY", _past(10))
    result = expiring_soon(secrets, within_seconds=86400)
    keys = [r["key"] for r in result]
    assert "API_KEY" not in keys


def test_expiring_soon_skips_internal_keys(secrets):
    secrets["__ttl"] = {}
    result = expiring_soon(secrets, within_seconds=86400)
    assert all(not r["key"].startswith("__") for r in result)


def test_expiring_soon_result_has_expected_fields(secrets):
    set_ttl(secrets, "TOKEN", _future(100))
    result = expiring_soon(secrets, within_seconds=86400)
    match = next(r for r in result if r["key"] == "TOKEN")
    assert "expires_at" in match
    assert "seconds_remaining" in match
    assert match["seconds_remaining"] > 0


# --- rotation_overdue ---

def test_rotation_overdue_includes_stale_key(secrets):
    old_time = _past(90 * 86400).isoformat()
    set_rotation_metadata(secrets, "DB_PASS", {"last_rotated": old_time, "interval_days": 30})
    result = rotation_overdue(secrets)
    keys = [r["key"] for r in result]
    assert "DB_PASS" in keys


def test_rotation_overdue_excludes_fresh_key(secrets):
    recent_time = _past(1).isoformat()
    set_rotation_metadata(secrets, "DB_PASS", {"last_rotated": recent_time, "interval_days": 30})
    result = rotation_overdue(secrets)
    keys = [r["key"] for r in result]
    assert "DB_PASS" not in keys


def test_rotation_overdue_skips_internal_keys(secrets):
    secrets["__rotation"] = {}
    result = rotation_overdue(secrets)
    assert all(not r["key"].startswith("__") for r in result)


# --- reminder_report ---

def test_reminder_report_structure(secrets):
    report = reminder_report(secrets)
    assert "expiring_soon" in report
    assert "rotation_overdue" in report
    assert isinstance(report["expiring_soon"], list)
    assert isinstance(report["rotation_overdue"], list)
