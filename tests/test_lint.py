"""Tests for envault.lint."""

from __future__ import annotations

import pytest

from envault.lint import LintIssue, LintReport, lint_secrets
from envault.schema import set_schema
from envault.ttl import set_ttl
from envault.tags import add_tag
from envault.notes import set_note


@pytest.fixture()
def secrets() -> dict:
    base = {"API_KEY": "abc123", "DB_PASS": "s3cr3t"}
    return base


# ---------------------------------------------------------------------------
# LintReport helpers
# ---------------------------------------------------------------------------

def test_lint_report_errors_filter():
    report = LintReport(issues=[
        LintIssue("K", "error", "bad"),
        LintIssue("K", "warning", "meh"),
        LintIssue("K", "info", "ok"),
    ])
    assert len(report.errors) == 1
    assert len(report.warnings) == 1
    assert report.has_errors


def test_lint_report_summary_format():
    report = LintReport(issues=[
        LintIssue("A", "error", "e"),
        LintIssue("B", "warning", "w"),
        LintIssue("C", "info", "i"),
    ])
    summary = report.summary()
    assert "1 error" in summary
    assert "1 warning" in summary
    assert "1 info" in summary


# ---------------------------------------------------------------------------
# Schema checks
# ---------------------------------------------------------------------------

def test_lint_flags_missing_schema_as_info(secrets):
    report = lint_secrets(secrets, check_schema=True, check_ttl=False, check_tags=False)
    info_keys = {i.key for i in report.issues if i.level == "info"}
    assert "API_KEY" in info_keys
    assert "DB_PASS" in info_keys


def test_lint_schema_violation_is_error(secrets):
    set_schema(secrets, "API_KEY", value_type="integer")
    report = lint_secrets(secrets, check_schema=True, check_ttl=False, check_tags=False)
    errors = [i for i in report.issues if i.key == "API_KEY" and i.level == "error"]
    assert errors, "expected a schema error for API_KEY"


def test_lint_valid_schema_no_error(secrets):
    set_schema(secrets, "API_KEY", value_type="string")
    report = lint_secrets(secrets, check_schema=True, check_ttl=False, check_tags=False)
    errors = [i for i in report.issues if i.key == "API_KEY" and i.level == "error"]
    assert not errors


# ---------------------------------------------------------------------------
# TTL checks
# ---------------------------------------------------------------------------

def test_lint_flags_missing_ttl_as_warning(secrets):
    report = lint_secrets(secrets, check_schema=False, check_ttl=True, check_tags=False)
    warnings = {i.key for i in report.issues if i.level == "warning"}
    assert "API_KEY" in warnings


def test_lint_expired_ttl_is_error(secrets):
    import time
    set_ttl(secrets, "API_KEY", expires_at=time.time() - 1)
    report = lint_secrets(secrets, check_schema=False, check_ttl=True, check_tags=False)
    errors = [i for i in report.issues if i.key == "API_KEY" and i.level == "error"]
    assert errors


def test_lint_valid_ttl_no_warning(secrets):
    import time
    set_ttl(secrets, "API_KEY", expires_at=time.time() + 9999)
    report = lint_secrets(secrets, check_schema=False, check_ttl=True, check_tags=False)
    ttl_issues = [i for i in report.issues if i.key == "API_KEY"]
    assert not any(i.level in ("warning", "error") for i in ttl_issues)


# ---------------------------------------------------------------------------
# Tags / notes checks
# ---------------------------------------------------------------------------

def test_lint_missing_tags_is_info(secrets):
    report = lint_secrets(secrets, check_schema=False, check_ttl=False, check_tags=True)
    info_keys = {i.key for i in report.issues if i.level == "info"}
    assert "API_KEY" in info_keys


def test_lint_tagged_key_no_info(secrets):
    add_tag(secrets, "API_KEY", "production")
    report = lint_secrets(secrets, check_schema=False, check_ttl=False, check_tags=True)
    tag_info = [i for i in report.issues if i.key == "API_KEY" and "tag" in i.message]
    assert not tag_info


def test_lint_internal_keys_skipped(secrets):
    secrets["__rotation_meta"] = "{}"
    report = lint_secrets(secrets, check_schema=True, check_ttl=True, check_tags=True)
    internal_issues = [i for i in report.issues if i.key == "__rotation_meta"]
    assert not internal_issues


def test_lint_notes_check_disabled_by_default(secrets):
    report = lint_secrets(secrets, check_schema=False, check_ttl=False, check_tags=False)
    note_issues = [i for i in report.issues if "note" in i.message.lower()]
    assert not note_issues


def test_lint_notes_enabled_flags_missing(secrets):
    report = lint_secrets(
        secrets, check_schema=False, check_ttl=False, check_tags=False, check_notes=True
    )
    note_info = [i for i in report.issues if "note" in i.message.lower()]
    assert note_info
