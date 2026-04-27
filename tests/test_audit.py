"""Tests for envault.audit module."""

import json
import pytest
from pathlib import Path

from envault.audit import (
    record_event,
    read_events,
    filter_events,
    AUDIT_LOG_FILENAME,
)


@pytest.fixture
def vault_dir(tmp_path):
    return str(tmp_path)


def test_record_event_creates_log_file(vault_dir):
    record_event(vault_dir, action="set", key="DB_PASSWORD")
    log_path = Path(vault_dir) / AUDIT_LOG_FILENAME
    assert log_path.exists()


def test_record_event_contains_expected_fields(vault_dir):
    record_event(vault_dir, action="get", key="API_KEY", actor="alice", note="deploy")
    events = read_events(vault_dir)
    assert len(events) == 1
    e = events[0]
    assert e["action"] == "get"
    assert e["key"] == "API_KEY"
    assert e["actor"] == "alice"
    assert e["note"] == "deploy"
    assert "timestamp" in e


def test_multiple_events_appended_in_order(vault_dir):
    record_event(vault_dir, action="set", key="FOO")
    record_event(vault_dir, action="rotate", key="FOO")
    record_event(vault_dir, action="get", key="BAR")
    events = read_events(vault_dir)
    assert len(events) == 3
    assert events[0]["action"] == "set"
    assert events[1]["action"] == "rotate"
    assert events[2]["action"] == "get"


def test_read_events_returns_empty_list_when_no_log(vault_dir):
    events = read_events(vault_dir)
    assert events == []


def test_filter_events_by_action(vault_dir):
    record_event(vault_dir, action="set", key="X")
    record_event(vault_dir, action="get", key="X")
    record_event(vault_dir, action="get", key="Y")
    all_events = read_events(vault_dir)
    gets = filter_events(all_events, action="get")
    assert len(gets) == 2
    assert all(e["action"] == "get" for e in gets)


def test_filter_events_by_key(vault_dir):
    record_event(vault_dir, action="set", key="SECRET_A")
    record_event(vault_dir, action="set", key="SECRET_B")
    all_events = read_events(vault_dir)
    filtered = filter_events(all_events, key="SECRET_A")
    assert len(filtered) == 1
    assert filtered[0]["key"] == "SECRET_A"


def test_filter_events_by_action_and_key(vault_dir):
    record_event(vault_dir, action="set", key="TOKEN")
    record_event(vault_dir, action="get", key="TOKEN")
    record_event(vault_dir, action="get", key="OTHER")
    all_events = read_events(vault_dir)
    result = filter_events(all_events, action="get", key="TOKEN")
    assert len(result) == 1
    assert result[0]["action"] == "get"
    assert result[0]["key"] == "TOKEN"


def test_each_event_is_valid_json_line(vault_dir):
    record_event(vault_dir, action="delete", key="OLD_KEY")
    log_path = Path(vault_dir) / AUDIT_LOG_FILENAME
    lines = log_path.read_text().strip().splitlines()
    for line in lines:
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
