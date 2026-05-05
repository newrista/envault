"""Tests for envault.verify."""

from __future__ import annotations

import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

from envault.verify import verify_secrets, VerifyReport, VerifyIssue


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret"}


def test_verify_returns_report_type(secrets):
    report = verify_secrets(secrets)
    assert isinstance(report, VerifyReport)


def test_no_schema_produces_info(secrets):
    report = verify_secrets(secrets)
    infos = [i for i in report.issues if i.level == "info"]
    assert any(i.key == "API_KEY" for i in infos)


def test_schema_violation_produces_error(secrets):
    secrets["PORT"] = "not-a-number"
    with patch("envault.verify.get_schema", return_value={"type": "integer"}):
        with patch("envault.verify.validate_value", side_effect=Exception("type mismatch")) as mock_val:
            from envault.schema import SchemaValidationError
            mock_val.side_effect = SchemaValidationError("PORT", "type mismatch")
            report = verify_secrets(secrets)
    errors = [i for i in report.issues if i.level == "error" and i.key == "PORT"]
    assert errors, "Expected a schema error for PORT"


def test_expired_ttl_produces_warning(secrets):
    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with patch("envault.verify.is_expired", return_value=True):
        with patch("envault.verify.get_ttl", return_value=past):
            with patch("envault.verify.get_schema", return_value=None):
                report = verify_secrets(secrets)
    warnings = [i for i in report.issues if i.level == "warning"]
    assert len(warnings) == len(secrets)


def test_pinned_empty_value_produces_error():
    data = {"TOKEN": ""}
    with patch("envault.verify.is_pinned", return_value=True):
        with patch("envault.verify.is_expired", return_value=False):
            with patch("envault.verify.get_schema", return_value=None):
                report = verify_secrets(data)
    errors = [i for i in report.issues if i.level == "error" and i.key == "TOKEN"]
    assert errors


def test_internal_keys_are_skipped():
    data = {"__rotation_meta": "...", "NORMAL": "value"}
    with patch("envault.verify.get_schema", return_value=None):
        with patch("envault.verify.is_expired", return_value=False):
            with patch("envault.verify.is_pinned", return_value=False):
                report = verify_secrets(data)
    keys_reported = {i.key for i in report.issues}
    assert "__rotation_meta" not in keys_reported
    assert "NORMAL" in keys_reported


def test_report_has_errors_true_when_errors_present():
    report = VerifyReport(issues=[VerifyIssue(key="X", level="error", message="bad")])
    assert report.has_errors() is True


def test_report_has_errors_false_when_only_warnings():
    report = VerifyReport(issues=[VerifyIssue(key="X", level="warning", message="meh")])
    assert report.has_errors() is False


def test_report_summary_format():
    report = VerifyReport(
        issues=[
            VerifyIssue(key="A", level="error", message="e"),
            VerifyIssue(key="B", level="warning", message="w"),
            VerifyIssue(key="C", level="info", message="i"),
        ]
    )
    assert report.summary() == "1 error(s), 1 warning(s)"
