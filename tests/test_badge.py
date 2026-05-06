"""Tests for envault.badge."""

from __future__ import annotations

import pytest

from envault.badge import (
    _shield_url,
    secret_status_badge,
    vault_health_badge,
    generate_badges,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def secrets() -> dict:
    """Minimal vault-like dict with a few plain secrets."""
    return {
        "DB_HOST": "localhost",
        "DB_PASS": "s3cr3t",
        "API_KEY": "abc123",
        "__ttl_index": {},
    }


# ---------------------------------------------------------------------------
# _shield_url
# ---------------------------------------------------------------------------

def test_shield_url_contains_label_and_message():
    url = _shield_url("vault", "healthy", "brightgreen")
    assert "vault" in url
    assert "healthy" in url
    assert "brightgreen" in url


def test_shield_url_escapes_spaces():
    url = _shield_url("my label", "all good", "green")
    assert " " not in url


def test_shield_url_escapes_hyphens():
    url = _shield_url("my-label", "ok", "green")
    # hyphens become double-hyphens in shields.io convention
    assert "--" in url


# ---------------------------------------------------------------------------
# secret_status_badge
# ---------------------------------------------------------------------------

def test_secret_status_badge_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        secret_status_badge(secrets, "NONEXISTENT")


def test_secret_status_badge_unmanaged_key(secrets):
    badge = secret_status_badge(secrets, "DB_HOST")
    assert badge["message"] == "unmanaged"
    assert badge["colour"] == "lightgrey"
    assert badge["label"] == "DB_HOST"
    assert "shields.io" in badge["url"]


def test_secret_status_badge_pinned_key(secrets):
    from envault.pin import pin_secret
    pin_secret(secrets, "DB_PASS", reason="critical")
    badge = secret_status_badge(secrets, "DB_PASS")
    assert badge["message"] == "pinned"
    assert badge["colour"] == "blue"


def test_secret_status_badge_expired_key(secrets):
    import time
    from envault.ttl import set_ttl
    set_ttl(secrets, "API_KEY", ttl_seconds=-1)  # already expired
    badge = secret_status_badge(secrets, "API_KEY")
    assert badge["message"] == "expired"
    assert badge["colour"] == "red"


def test_secret_status_badge_returns_url(secrets):
    badge = secret_status_badge(secrets, "DB_HOST")
    assert badge["url"].startswith("https://img.shields.io/badge/")


# ---------------------------------------------------------------------------
# vault_health_badge
# ---------------------------------------------------------------------------

def test_vault_health_badge_healthy(secrets):
    badge = vault_health_badge(secrets)
    assert badge["label"] == "vault"
    assert badge["colour"] == "brightgreen"
    assert badge["message"] == "healthy"


def test_vault_health_badge_has_url(secrets):
    badge = vault_health_badge(secrets)
    assert "shields.io" in badge["url"]


# ---------------------------------------------------------------------------
# generate_badges
# ---------------------------------------------------------------------------

def test_generate_badges_returns_list(secrets):
    badges = generate_badges(secrets)
    assert isinstance(badges, list)
    assert len(badges) == 3  # DB_HOST, DB_PASS, API_KEY (not __ttl_index)


def test_generate_badges_excludes_internal_keys(secrets):
    badges = generate_badges(secrets)
    labels = [b["label"] for b in badges]
    assert "__ttl_index" not in labels


def test_generate_badges_with_explicit_keys(secrets):
    badges = generate_badges(secrets, keys=["DB_HOST"])
    assert len(badges) == 1
    assert badges[0]["label"] == "DB_HOST"
