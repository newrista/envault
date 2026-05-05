"""Tests for envault.watch."""

from __future__ import annotations

import json
import pytest

from envault.watch import (
    _secret_fingerprint,
    detect_changes,
    get_watch_state,
    save_watch_state,
    watch_secrets,
)


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret"}


# ---------------------------------------------------------------------------
# _secret_fingerprint
# ---------------------------------------------------------------------------

def test_fingerprint_excludes_internal_keys(secrets):
    secrets["__watch_state__"] = "{}"
    fp = _secret_fingerprint(secrets)
    assert "__watch_state__" not in fp
    assert "API_KEY" in fp


def test_fingerprint_is_deterministic(secrets):
    assert _secret_fingerprint(secrets) == _secret_fingerprint(secrets)


def test_fingerprint_changes_when_value_changes(secrets):
    fp1 = _secret_fingerprint(secrets)
    secrets["API_KEY"] = "new_value"
    fp2 = _secret_fingerprint(secrets)
    assert fp1["API_KEY"] != fp2["API_KEY"]
    assert fp1["DB_PASS"] == fp2["DB_PASS"]


# ---------------------------------------------------------------------------
# get_watch_state / save_watch_state
# ---------------------------------------------------------------------------

def test_get_watch_state_returns_empty_when_missing(secrets):
    assert get_watch_state(secrets) == {}


def test_save_and_get_watch_state_roundtrip(secrets):
    state = {"API_KEY": "deadbeef"}
    save_watch_state(secrets, state)
    assert get_watch_state(secrets) == state


def test_get_watch_state_handles_corrupt_json(secrets):
    secrets["__watch_state__"] = "not-json"
    assert get_watch_state(secrets) == {}


# ---------------------------------------------------------------------------
# detect_changes
# ---------------------------------------------------------------------------

def test_detect_changes_added(secrets):
    save_watch_state(secrets, _secret_fingerprint(secrets))
    secrets["NEW_KEY"] = "new_value"
    changes = detect_changes(secrets)
    assert changes.get("NEW_KEY") == "added"


def test_detect_changes_removed(secrets):
    save_watch_state(secrets, _secret_fingerprint(secrets))
    del secrets["DB_PASS"]
    changes = detect_changes(secrets)
    assert changes.get("DB_PASS") == "removed"


def test_detect_changes_modified(secrets):
    save_watch_state(secrets, _secret_fingerprint(secrets))
    secrets["API_KEY"] = "totally_different"
    changes = detect_changes(secrets)
    assert changes.get("API_KEY") == "modified"


def test_detect_changes_none_when_unchanged(secrets):
    save_watch_state(secrets, _secret_fingerprint(secrets))
    assert detect_changes(secrets) == {}


# ---------------------------------------------------------------------------
# watch_secrets
# ---------------------------------------------------------------------------

def test_watch_secrets_calls_callback_on_change(secrets):
    save_watch_state(secrets, _secret_fingerprint(secrets))
    secrets["API_KEY"] = "changed!"

    seen = []
    watch_secrets(secrets, callback=lambda k, t: seen.append((k, t)), iterations=1)
    assert ("API_KEY", "modified") in seen


def test_watch_secrets_no_callback_when_stable(secrets):
    save_watch_state(secrets, _secret_fingerprint(secrets))
    seen = []
    watch_secrets(secrets, callback=lambda k, t: seen.append((k, t)), iterations=1)
    assert seen == []
