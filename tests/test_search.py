"""Tests for envault.search module."""

from __future__ import annotations

import pytest

from envault.search import search_keys, search_secrets, search_values

SECRETS = {
    "DATABASE_URL": "postgres://localhost/mydb",
    "DATABASE_PASSWORD": "s3cr3t",
    "API_KEY": "abcdef123456",
    "API_SECRET": "xyz987",
    "REDIS_URL": "redis://localhost:6379",
    "DEBUG": "true",
}


# ---------------------------------------------------------------------------
# search_keys
# ---------------------------------------------------------------------------

def test_search_keys_glob_prefix():
    result = search_keys(SECRETS, "DATABASE_*")
    assert result == ["DATABASE_PASSWORD", "DATABASE_URL"]


def test_search_keys_glob_wildcard():
    result = search_keys(SECRETS, "*URL*")
    assert "DATABASE_URL" in result
    assert "REDIS_URL" in result


def test_search_keys_no_match_returns_empty():
    result = search_keys(SECRETS, "NONEXISTENT_*")
    assert result == []


def test_search_keys_regex():
    result = search_keys(SECRETS, r"^API_", use_regex=True)
    assert result == ["API_KEY", "API_SECRET"]


def test_search_keys_invalid_regex_raises():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        search_keys(SECRETS, "[invalid", use_regex=True)


# ---------------------------------------------------------------------------
# search_values
# ---------------------------------------------------------------------------

def test_search_values_glob():
    result = search_values(SECRETS, "*localhost*")
    keys = [k for k, _ in result]
    assert "DATABASE_URL" in keys
    assert "REDIS_URL" in keys


def test_search_values_regex():
    result = search_values(SECRETS, r"\d{4,}", use_regex=True)
    keys = [k for k, _ in result]
    assert "API_KEY" in keys  # abcdef123456 contains 6 digits


def test_search_values_no_match_returns_empty():
    result = search_values(SECRETS, "*NOTHING*")
    assert result == []


def test_search_values_invalid_regex_raises():
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        search_values(SECRETS, "[bad", use_regex=True)


# ---------------------------------------------------------------------------
# search_secrets (combined)
# ---------------------------------------------------------------------------

def test_search_secrets_keys_only():
    result = search_secrets(SECRETS, "REDIS_*")
    assert list(result.keys()) == ["REDIS_URL"]
    assert result["REDIS_URL"] == "redis://localhost:6379"


def test_search_secrets_includes_values_when_flag_set():
    # Pattern matches value of DEBUG but not its key
    result = search_secrets(SECRETS, "true", search_values_too=True)
    assert "DEBUG" in result


def test_search_secrets_combined_deduplicates():
    # DATABASE_URL key matches glob AND its value contains 'localhost'
    result = search_secrets(
        SECRETS, "*DATABASE*", search_values_too=True
    )
    keys = list(result.keys())
    assert keys.count("DATABASE_URL") == 1


def test_search_secrets_returns_sorted_keys():
    result = search_secrets(SECRETS, "*", search_values_too=False)
    assert list(result.keys()) == sorted(SECRETS.keys())
