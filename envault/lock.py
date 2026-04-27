"""Vault locking mechanism to prevent concurrent access and enforce TTL-based auto-lock."""

import json
import os
import time
from pathlib import Path

LOCK_FILENAME = ".vault.lock"
DEFAULT_TTL_SECONDS = 300  # 5 minutes


def _lock_path(vault_dir: str) -> Path:
    return Path(vault_dir) / LOCK_FILENAME


def acquire_lock(vault_dir: str, session_id: str, ttl: int = DEFAULT_TTL_SECONDS) -> bool:
    """Acquire a lock for the vault. Returns True if lock was acquired, False if already locked."""
    lock_file = _lock_path(vault_dir)

    if lock_file.exists():
        try:
            data = json.loads(lock_file.read_text())
            locked_at = data.get("locked_at", 0)
            existing_ttl = data.get("ttl", DEFAULT_TTL_SECONDS)
            if time.time() - locked_at < existing_ttl:
                if data.get("session_id") != session_id:
                    return False  # Locked by another session
        except (json.JSONDecodeError, KeyError):
            pass  # Corrupt lock file — overwrite it

    lock_data = {
        "session_id": session_id,
        "locked_at": time.time(),
        "ttl": ttl,
    }
    lock_file.write_text(json.dumps(lock_data))
    return True


def release_lock(vault_dir: str, session_id: str) -> bool:
    """Release the lock if it belongs to the given session. Returns True if released."""
    lock_file = _lock_path(vault_dir)
    if not lock_file.exists():
        return False
    try:
        data = json.loads(lock_file.read_text())
        if data.get("session_id") == session_id:
            lock_file.unlink()
            return True
    except (json.JSONDecodeError, KeyError):
        pass
    return False


def is_locked(vault_dir: str) -> bool:
    """Check whether the vault is currently locked (and lock has not expired)."""
    lock_file = _lock_path(vault_dir)
    if not lock_file.exists():
        return False
    try:
        data = json.loads(lock_file.read_text())
        locked_at = data.get("locked_at", 0)
        ttl = data.get("ttl", DEFAULT_TTL_SECONDS)
        if time.time() - locked_at < ttl:
            return True
        lock_file.unlink()  # Expired lock — clean up
    except (json.JSONDecodeError, KeyError):
        pass
    return False


def lock_info(vault_dir: str) -> dict | None:
    """Return lock metadata if vault is locked, else None."""
    lock_file = _lock_path(vault_dir)
    if not lock_file.exists():
        return None
    try:
        data = json.loads(lock_file.read_text())
        locked_at = data.get("locked_at", 0)
        ttl = data.get("ttl", DEFAULT_TTL_SECONDS)
        if time.time() - locked_at < ttl:
            data["expires_in"] = int(ttl - (time.time() - locked_at))
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None
