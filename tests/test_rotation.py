"""Tests for secret rotation utilities."""

import pytest
from datetime import datetime, timedelta
from envault.rotation import (
    rotate_secret,
    is_rotation_due,
    list_stale_secrets,
    set_rotation_metadata,
    get_rotation_metadata,
    ROTATION_METADATA_KEY,
)


@pytest.fixture
def fresh_secrets():
    return {"DB_PASSWORD": "old_pass", "API_KEY": "old_key"}


def test_rotate_secret_updates_value(fresh_secrets):
    updated = rotate_secret(fresh_secrets, "DB_PASSWORD", "new_pass")
    assert updated["DB_PASSWORD"] == "new_pass"


def test_rotate_secret_records_timestamp(fresh_secrets):
    updated = rotate_secret(fresh_secrets, "DB_PASSWORD", "new_pass")
    meta = get_rotation_metadata(updated)
    assert "DB_PASSWORD" in meta


def test_rotate_reserved_key_raises(fresh_secrets):
    with pytest.raises(ValueError, match="reserved"):
        rotate_secret(fresh_secrets, ROTATION_METADATA_KEY, "x")


def test_is_rotation_due_with_no_metadata(fresh_secrets):
    assert is_rotation_due(fresh_secrets, "DB_PASSWORD") is True


def test_is_rotation_due_after_recent_rotation(fresh_secrets):
    updated = rotate_secret(fresh_secrets, "DB_PASSWORD", "new_pass")
    assert is_rotation_due(updated, "DB_PASSWORD", max_age_days=90) is False


def test_is_rotation_due_after_old_rotation(fresh_secrets):
    old_time = datetime.utcnow() - timedelta(days=100)
    updated = set_rotation_metadata(fresh_secrets, "DB_PASSWORD", rotated_at=old_time)
    assert is_rotation_due(updated, "DB_PASSWORD", max_age_days=90) is True


def test_list_stale_secrets_returns_unrotated(fresh_secrets):
    stale = list_stale_secrets(fresh_secrets, max_age_days=90)
    assert "DB_PASSWORD" in stale
    assert "API_KEY" in stale


def test_list_stale_secrets_excludes_fresh_keys(fresh_secrets):
    updated = rotate_secret(fresh_secrets, "DB_PASSWORD", "new_pass")
    stale = list_stale_secrets(updated, max_age_days=90)
    assert "DB_PASSWORD" not in stale
    assert "API_KEY" in stale


def test_list_stale_excludes_metadata_key(fresh_secrets):
    stale = list_stale_secrets(fresh_secrets)
    assert ROTATION_METADATA_KEY not in stale
