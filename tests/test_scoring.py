"""Tests for envault.scoring."""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from envault.scoring import score_vault, ScoreReport


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _future(days: int = 30) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _past(days: int = 1) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


@pytest.fixture()
def clean_secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret"}


# ---------------------------------------------------------------------------
# basic
# ---------------------------------------------------------------------------

def test_empty_vault_returns_perfect_score():
    report = score_vault({})
    assert report.score == 100.0
    assert report.total_keys == 0


def test_clean_vault_returns_perfect_score(clean_secrets):
    report = score_vault(clean_secrets)
    assert report.score == 100.0
    assert report.total_keys == 2


def test_internal_keys_excluded_from_total():
    secrets = {"MY_KEY": "val", "__meta": "internal"}
    report = score_vault(secrets)
    assert report.total_keys == 1


# ---------------------------------------------------------------------------
# expired TTL penalty
# ---------------------------------------------------------------------------

def test_expired_ttl_reduces_score(clean_secrets):
    clean_secrets["__ttl__"] = f'{{"API_KEY": "{_past(1)}", "DB_PASS": "{_future(10)}"}}'.replace("'", '"')
    # inject via the real ttl index format
    import json
    clean_secrets["__ttl__"] = json.dumps({"API_KEY": _past(1)})
    report = score_vault(clean_secrets)
    assert report.expired_count == 1
    assert report.score == pytest.approx(90.0)


def test_two_expired_keys_reduce_score_by_twenty():
    import json
    secrets = {"A": "1", "B": "2", "__ttl__": json.dumps({"A": _past(2), "B": _past(1)})}
    report = score_vault(secrets)
    assert report.expired_count == 2
    assert report.score == pytest.approx(80.0)


# ---------------------------------------------------------------------------
# score report helpers
# ---------------------------------------------------------------------------

def test_score_report_summary_contains_grade():
    report = ScoreReport(total_keys=5, score=95.0)
    assert "Grade A" in report.summary()


def test_score_report_grade_f_below_40():
    report = ScoreReport(total_keys=5, score=35.0)
    assert "Grade F" in report.summary()


def test_score_clamped_at_zero():
    import json
    # 11 expired keys * 10 pts each = 110 pts penalty → clamped to 0
    keys = {str(i): "v" for i in range(11)}
    keys["__ttl__"] = json.dumps({str(i): _past(1) for i in range(11)})
    report = score_vault(keys)
    assert report.score == 0.0


def test_breakdown_keys_present(clean_secrets):
    report = score_vault(clean_secrets)
    assert "expired_penalty" in report.breakdown
    assert "stale_penalty" in report.breakdown
    assert "no_schema_penalty" in report.breakdown
