"""Tests for envault.redact."""

import pytest

from envault.redact import mask_value, redact_secrets, redact_string


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_returns_default_mask():
    assert mask_value("supersecret") == "****"


def test_mask_value_custom_mask():
    assert mask_value("supersecret", mask="[REDACTED]") == "[REDACTED]"


def test_mask_value_reveal_chars_shows_suffix():
    result = mask_value("supersecret", reveal_chars=3)
    assert result == "****ret"


def test_mask_value_reveal_chars_longer_than_value_returns_mask_only():
    result = mask_value("ab", reveal_chars=5)
    assert result == "****"


def test_mask_value_empty_string_returns_mask():
    assert mask_value("") == "****"


# ---------------------------------------------------------------------------
# redact_secrets
# ---------------------------------------------------------------------------

@pytest.fixture()
def secrets():
    return {"DB_PASS": "hunter2", "API_KEY": "abc123", "HOST": "localhost"}


def test_redact_secrets_masks_all_values(secrets):
    result = redact_secrets(secrets)
    assert result["DB_PASS"] == "****"
    assert result["API_KEY"] == "****"
    assert result["HOST"] == "****"


def test_redact_secrets_specific_keys(secrets):
    result = redact_secrets(secrets, keys=["DB_PASS"])
    assert result["DB_PASS"] == "****"
    assert result["API_KEY"] == "abc123"  # unchanged
    assert result["HOST"] == "localhost"  # unchanged


def test_redact_secrets_skips_internal_keys():
    data = {"__meta": "internal", "SECRET": "value"}
    result = redact_secrets(data)
    assert result["__meta"] == "internal"
    assert result["SECRET"] == "****"


def test_redact_secrets_does_not_skip_internal_when_flag_false():
    data = {"__meta": "internal"}
    result = redact_secrets(data, skip_internal=False)
    assert result["__meta"] == "****"


def test_redact_secrets_reveal_chars(secrets):
    result = redact_secrets(secrets, keys=["DB_PASS"], reveal_chars=2)
    assert result["DB_PASS"] == "****r2"


def test_redact_secrets_custom_mask(secrets):
    result = redact_secrets(secrets, mask="[HIDDEN]")
    for key in ("DB_PASS", "API_KEY", "HOST"):
        assert result[key] == "[HIDDEN]"


def test_redact_secrets_returns_new_dict(secrets):
    result = redact_secrets(secrets)
    assert result is not secrets


# ---------------------------------------------------------------------------
# redact_string
# ---------------------------------------------------------------------------

def test_redact_string_replaces_secret_in_text():
    text = "connecting with password hunter2 to db"
    result = redact_string(text, {"DB_PASS": "hunter2"})
    assert "hunter2" not in result
    assert "****" in result


def test_redact_string_multiple_secrets():
    text = "key=abc123 pass=hunter2"
    result = redact_string(text, {"API_KEY": "abc123", "DB_PASS": "hunter2"})
    assert "abc123" not in result
    assert "hunter2" not in result


def test_redact_string_skips_internal_keys():
    text = "value is internal"
    result = redact_string(text, {"__meta": "internal"})
    assert result == text  # unchanged


def test_redact_string_skips_empty_values():
    text = "nothing to replace here"
    result = redact_string(text, {"EMPTY": ""})
    assert result == text
