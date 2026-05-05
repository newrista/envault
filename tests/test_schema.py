"""Tests for envault.schema."""

import pytest

from envault.schema import (
    SchemaValidationError,
    add_tag,
    get_schema,
    remove_schema,
    set_schema,
    validate_all,
    validate_value,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def secrets():
    return {
        "API_URL": "https://example.com",
        "PORT": "8080",
        "DEBUG": "true",
        "RATIO": "3.14",
        "EMAIL": "admin@example.com",
        "CODE": "ABC-123",
    }


# ---------------------------------------------------------------------------
# set_schema / get_schema
# ---------------------------------------------------------------------------

def test_set_schema_stores_type(secrets):
    set_schema(secrets, "PORT", "integer")
    schema = get_schema(secrets, "PORT")
    assert schema == {"type": "integer"}


def test_set_schema_with_pattern(secrets):
    set_schema(secrets, "CODE", "regex", pattern=r"[A-Z]{3}-\d{3}")
    schema = get_schema(secrets, "CODE")
    assert schema["type"] == "regex"
    assert schema["pattern"] == r"[A-Z]{3}-\d{3}"


def test_set_schema_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        set_schema(secrets, "NONEXISTENT", "string")


def test_set_schema_invalid_type_raises(secrets):
    with pytest.raises(ValueError, match="Unknown schema type"):
        set_schema(secrets, "PORT", "uuid")


def test_set_schema_regex_without_pattern_raises(secrets):
    with pytest.raises(ValueError, match="pattern"):
        set_schema(secrets, "CODE", "regex")


def test_get_schema_returns_none_when_not_set(secrets):
    assert get_schema(secrets, "API_URL") is None


# ---------------------------------------------------------------------------
# remove_schema
# ---------------------------------------------------------------------------

def test_remove_schema_clears_entry(secrets):
    set_schema(secrets, "PORT", "integer")
    remove_schema(secrets, "PORT")
    assert get_schema(secrets, "PORT") is None


def test_remove_schema_noop_when_not_set(secrets):
    # Should not raise
    remove_schema(secrets, "PORT")


# ---------------------------------------------------------------------------
# validate_value
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["42", "-7", "0"])
def test_validate_integer_ok(value):
    validate_value({"type": "integer"}, value)


def test_validate_integer_fails():
    with pytest.raises(SchemaValidationError):
        validate_value({"type": "integer"}, "not_an_int")


@pytest.mark.parametrize("value", ["true", "false", "1", "0", "yes", "no", "True"])
def test_validate_boolean_ok(value):
    validate_value({"type": "boolean"}, value)


def test_validate_boolean_fails():
    with pytest.raises(SchemaValidationError):
        validate_value({"type": "boolean"}, "maybe")


def test_validate_url_ok():
    validate_value({"type": "url"}, "https://example.com/path")


def test_validate_url_fails():
    with pytest.raises(SchemaValidationError):
        validate_value({"type": "url"}, "ftp://old-school.net")


def test_validate_email_ok():
    validate_value({"type": "email"}, "user@domain.org")


def test_validate_email_fails():
    with pytest.raises(SchemaValidationError):
        validate_value({"type": "email"}, "not-an-email")


def test_validate_regex_ok():
    validate_value({"type": "regex", "pattern": r"\d{4}"}, "1234")


def test_validate_regex_fails():
    with pytest.raises(SchemaValidationError):
        validate_value({"type": "regex", "pattern": r"\d{4}"}, "abcd")


# ---------------------------------------------------------------------------
# validate_all
# ---------------------------------------------------------------------------

def test_validate_all_no_schemas_returns_empty(secrets):
    assert validate_all(secrets) == {}


def test_validate_all_returns_errors_for_invalid(secrets):
    set_schema(secrets, "PORT", "integer")
    secrets["PORT"] = "not_a_number"
    errors = validate_all(secrets)
    assert "PORT" in errors


def test_validate_all_passes_for_valid_values(secrets):
    set_schema(secrets, "PORT", "integer")
    set_schema(secrets, "API_URL", "url")
    errors = validate_all(secrets)
    assert errors == {}
