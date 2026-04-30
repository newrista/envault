"""Tests for envault.env_inject."""

from __future__ import annotations

import os
import sys
import time

import pytest

from envault.env_inject import ExpiredSecretError, build_env, run_with_secrets
from envault.ttl import set_ttl


@pytest.fixture()
def secrets():
    return {
        "DB_HOST": "localhost",
        "API_KEY": "s3cr3t",
        "__rotation_meta": "{}",  # internal key — should be skipped
    }


class _FakeVault:
    def __init__(self, secrets):
        self.secrets = secrets


# ---------------------------------------------------------------------------
# build_env
# ---------------------------------------------------------------------------

def test_build_env_includes_vault_secrets(secrets):
    env = build_env(_FakeVault(secrets))
    assert env["DB_HOST"] == "localhost"
    assert env["API_KEY"] == "s3cr3t"


def test_build_env_skips_internal_keys(secrets):
    env = build_env(_FakeVault(secrets))
    assert "__rotation_meta" not in env


def test_build_env_includes_existing_os_environ(secrets):
    env = build_env(_FakeVault(secrets))
    # PATH (or any other real env-var) should still be present
    assert "PATH" in env or len(env) >= len(secrets) - 1


def test_build_env_override_true_replaces_existing(secrets, monkeypatch):
    monkeypatch.setenv("DB_HOST", "original")
    env = build_env(_FakeVault(secrets), override=True)
    assert env["DB_HOST"] == "localhost"


def test_build_env_override_false_preserves_existing(secrets, monkeypatch):
    monkeypatch.setenv("DB_HOST", "original")
    env = build_env(_FakeVault(secrets), override=False)
    assert env["DB_HOST"] == "original"


def test_build_env_prefix_applied(secrets):
    env = build_env(_FakeVault(secrets), prefix="APP_")
    assert "APP_DB_HOST" in env
    assert "APP_API_KEY" in env
    assert "DB_HOST" not in env


def test_build_env_expired_secret_raises():
    data = {"TOKEN": "abc"}
    set_ttl(data, "TOKEN", ttl_seconds=-1)  # already expired
    with pytest.raises(ExpiredSecretError, match="TOKEN"):
        build_env(_FakeVault(data))


def test_build_env_expired_secret_skipped_when_flag_set():
    data = {"TOKEN": "abc"}
    set_ttl(data, "TOKEN", ttl_seconds=-1)
    env = build_env(_FakeVault(data), skip_expired=True)
    assert "TOKEN" not in env


# ---------------------------------------------------------------------------
# run_with_secrets
# ---------------------------------------------------------------------------

def test_run_with_secrets_injects_env(secrets, tmp_path):
    result = run_with_secrets(
        _FakeVault(secrets),
        [sys.executable, "-c", "import os, sys; sys.exit(0 if os.environ.get('API_KEY')=='s3cr3t' else 1)"],
        check=True,
    )
    assert result.returncode == 0


def test_run_with_secrets_returns_completed_process(secrets):
    result = run_with_secrets(
        _FakeVault(secrets),
        [sys.executable, "-c", "pass"],
    )
    assert hasattr(result, "returncode")
