"""Tests for envault.notes."""

import pytest

from envault.notes import (
    NOTES_KEY,
    get_note,
    list_notes,
    remove_note,
    set_note,
)


@pytest.fixture()
def secrets():
    """Minimal secrets dict that mimics what Vault.load() returns."""
    return {"DB_HOST": "localhost", "API_KEY": "s3cr3t"}


# ---------------------------------------------------------------------------
# set_note
# ---------------------------------------------------------------------------

def test_set_note_attaches_note(secrets):
    set_note(secrets, "DB_HOST", "Primary database hostname")
    assert secrets[NOTES_KEY]["DB_HOST"] == "Primary database hostname"


def test_set_note_multiple_keys(secrets):
    set_note(secrets, "DB_HOST", "note A")
    set_note(secrets, "API_KEY", "note B")
    assert secrets[NOTES_KEY]["DB_HOST"] == "note A"
    assert secrets[NOTES_KEY]["API_KEY"] == "note B"


def test_set_note_overwrites_existing(secrets):
    set_note(secrets, "DB_HOST", "old note")
    set_note(secrets, "DB_HOST", "new note")
    assert secrets[NOTES_KEY]["DB_HOST"] == "new note"


def test_set_note_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING_KEY"):
        set_note(secrets, "MISSING_KEY", "this should fail")


# ---------------------------------------------------------------------------
# get_note
# ---------------------------------------------------------------------------

def test_get_note_returns_note(secrets):
    set_note(secrets, "API_KEY", "Do not share")
    assert get_note(secrets, "API_KEY") == "Do not share"


def test_get_note_returns_none_when_not_set(secrets):
    assert get_note(secrets, "DB_HOST") is None


def test_get_note_returns_none_for_unknown_key(secrets):
    assert get_note(secrets, "NONEXISTENT") is None


# ---------------------------------------------------------------------------
# remove_note
# ---------------------------------------------------------------------------

def test_remove_note_returns_true_when_removed(secrets):
    set_note(secrets, "DB_HOST", "to be removed")
    result = remove_note(secrets, "DB_HOST")
    assert result is True
    assert get_note(secrets, "DB_HOST") is None


def test_remove_note_returns_false_when_no_note(secrets):
    result = remove_note(secrets, "DB_HOST")
    assert result is False


# ---------------------------------------------------------------------------
# list_notes
# ---------------------------------------------------------------------------

def test_list_notes_empty_when_none_set(secrets):
    assert list_notes(secrets) == {}


def test_list_notes_returns_all_notes(secrets):
    set_note(secrets, "DB_HOST", "note 1")
    set_note(secrets, "API_KEY", "note 2")
    result = list_notes(secrets)
    assert result == {"DB_HOST": "note 1", "API_KEY": "note 2"}


def test_list_notes_returns_copy(secrets):
    set_note(secrets, "DB_HOST", "original")
    notes = list_notes(secrets)
    notes["DB_HOST"] = "mutated"
    # Original should be unchanged
    assert get_note(secrets, "DB_HOST") == "original"
