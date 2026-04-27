"""Tests for envault.lock — vault locking and TTL expiry."""

import time
import uuid

import pytest

from envault.lock import (
    acquire_lock,
    is_locked,
    lock_info,
    release_lock,
    LOCK_FILENAME,
)


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


def make_session():
    return str(uuid.uuid4())


def test_acquire_lock_succeeds_when_no_lock(vault_dir):
    session = make_session()
    assert acquire_lock(vault_dir, session) is True


def test_is_locked_after_acquire(vault_dir):
    session = make_session()
    acquire_lock(vault_dir, session)
    assert is_locked(vault_dir) is True


def test_is_not_locked_before_acquire(vault_dir):
    assert is_locked(vault_dir) is False


def test_acquire_lock_fails_for_different_session(vault_dir):
    session_a = make_session()
    session_b = make_session()
    acquire_lock(vault_dir, session_a)
    assert acquire_lock(vault_dir, session_b) is False


def test_same_session_can_reacquire(vault_dir):
    session = make_session()
    acquire_lock(vault_dir, session)
    assert acquire_lock(vault_dir, session) is True


def test_release_lock_removes_lock(vault_dir):
    session = make_session()
    acquire_lock(vault_dir, session)
    released = release_lock(vault_dir, session)
    assert released is True
    assert is_locked(vault_dir) is False


def test_release_lock_wrong_session_does_not_release(vault_dir):
    session_a = make_session()
    session_b = make_session()
    acquire_lock(vault_dir, session_a)
    assert release_lock(vault_dir, session_b) is False
    assert is_locked(vault_dir) is True


def test_release_nonexistent_lock_returns_false(vault_dir):
    assert release_lock(vault_dir, make_session()) is False


def test_lock_expires_after_ttl(vault_dir):
    session = make_session()
    acquire_lock(vault_dir, session, ttl=1)
    time.sleep(1.1)
    assert is_locked(vault_dir) is False


def test_lock_info_returns_metadata(vault_dir):
    session = make_session()
    acquire_lock(vault_dir, session, ttl=60)
    info = lock_info(vault_dir)
    assert info is not None
    assert info["session_id"] == session
    assert "locked_at" in info
    assert "expires_in" in info
    assert info["expires_in"] <= 60


def test_lock_info_returns_none_when_not_locked(vault_dir):
    assert lock_info(vault_dir) is None


def test_lock_file_created_in_vault_dir(vault_dir):
    from pathlib import Path
    session = make_session()
    acquire_lock(vault_dir, session)
    assert (Path(vault_dir) / LOCK_FILENAME).exists()
