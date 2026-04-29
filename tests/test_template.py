"""Tests for envault.template module."""

import pytest
from envault.template import (
    render,
    list_placeholders,
    render_dict,
    TemplateMissingKeyError,
)


SECRETS = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "API_KEY": "secret123",
}


def test_render_single_placeholder():
    result = render("host={{DB_HOST}}", SECRETS)
    assert result == "host=localhost"


def test_render_multiple_placeholders():
    result = render("{{DB_HOST}}:{{DB_PORT}}", SECRETS)
    assert result == "localhost:5432"


def test_render_no_placeholders():
    result = render("no substitution here", SECRETS)
    assert result == "no substitution here"


def test_render_placeholder_with_spaces():
    result = render("{{ DB_HOST }}", SECRETS)
    assert result == "localhost"


def test_render_strict_raises_on_missing_key():
    with pytest.raises(TemplateMissingKeyError, match="MISSING_KEY"):
        render("value={{MISSING_KEY}}", SECRETS, strict=True)


def test_render_non_strict_leaves_unresolved():
    result = render("value={{MISSING_KEY}}", SECRETS, strict=False)
    assert result == "value={{MISSING_KEY}}"


def test_render_repeated_placeholder_replaced_each_time():
    result = render("{{DB_HOST}} and {{DB_HOST}}", SECRETS)
    assert result == "localhost and localhost"


def test_list_placeholders_returns_unique_keys():
    placeholders = list_placeholders("{{DB_HOST}}:{{DB_PORT}} and {{DB_HOST}}")
    assert placeholders == ["DB_HOST", "DB_PORT"]


def test_list_placeholders_empty_template():
    assert list_placeholders("no placeholders") == []


def test_list_placeholders_ignores_invalid_names():
    # Numbers-only names don't match [A-Za-z_][...] pattern
    result = list_placeholders("{{123}} {{VALID_KEY}}")
    assert result == ["VALID_KEY"]


def test_render_dict_renders_all_values():
    templates = {
        "DSN": "postgresql://{{DB_HOST}}:{{DB_PORT}}/mydb",
        "AUTH": "Bearer {{API_KEY}}",
    }
    result = render_dict(templates, SECRETS)
    assert result["DSN"] == "postgresql://localhost:5432/mydb"
    assert result["AUTH"] == "Bearer secret123"


def test_render_dict_strict_raises_on_missing():
    templates = {"URL": "http://{{UNKNOWN_HOST}}"}
    with pytest.raises(TemplateMissingKeyError):
        render_dict(templates, SECRETS, strict=True)


def test_render_dict_non_strict_leaves_unresolved():
    templates = {"URL": "http://{{UNKNOWN_HOST}}"}
    result = render_dict(templates, SECRETS, strict=False)
    assert result["URL"] == "http://{{UNKNOWN_HOST}}"
