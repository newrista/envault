"""Tests for envault/import_secrets.py"""

import pytest
from envault.import_secrets import from_dotenv, from_json, from_shell, import_secrets


# --- from_dotenv ---

def test_dotenv_basic():
    content = "DB_HOST=localhost\nDB_PORT=5432\n"
    result = from_dotenv(content)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_dotenv_ignores_comments_and_blanks():
    content = "# comment\n\nAPI_KEY=secret\n"
    result = from_dotenv(content)
    assert result == {"API_KEY": "secret"}


def test_dotenv_strips_quotes():
    content = 'SECRET="my value"\nTOKEN=\'abc\'\n'
    result = from_dotenv(content)
    assert result["SECRET"] == "my value"
    assert result["TOKEN"] == "abc"


def test_dotenv_value_with_equals():
    content = "URL=http://example.com?foo=bar\n"
    result = from_dotenv(content)
    assert result["URL"] == "http://example.com?foo=bar"


# --- from_json ---

def test_json_basic():
    content = '{"KEY": "value", "NUM": 42}'
    result = from_json(content)
    assert result == {"KEY": "value", "NUM": "42"}


def test_json_non_dict_raises():
    with pytest.raises(ValueError, match="top-level object"):
        from_json('["a", "b"]')


def test_json_invalid_raises():
    with pytest.raises(Exception):
        from_json("not json")


# --- from_shell ---

def test_shell_basic():
    content = "export API_KEY=abc123\nexport DB_PASS=secret\n"
    result = from_shell(content)
    assert result == {"API_KEY": "abc123", "DB_PASS": "secret"}


def test_shell_ignores_non_export_lines():
    content = "# set vars\nexport FOO=bar\nBAZ=qux\n"
    result = from_shell(content)
    assert "FOO" in result
    assert "BAZ" not in result


# --- import_secrets auto-detection ---

def test_auto_detect_json():
    content = '{"A": "1"}'
    result = import_secrets(content)
    assert result == {"A": "1"}


def test_auto_detect_shell():
    content = "export X=hello\n"
    result = import_secrets(content)
    assert result == {"X": "hello"}


def test_auto_detect_dotenv():
    content = "MYVAR=myvalue\n"
    result = import_secrets(content)
    assert result == {"MYVAR": "myvalue"}


def test_explicit_format_override():
    content = "KEY=value\n"
    result = import_secrets(content, fmt="dotenv")
    assert result["KEY"] == "value"


def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        import_secrets("data", fmt="xml")
