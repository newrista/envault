"""Tests for envault.watermark."""

from __future__ import annotations

import pytest

from envault.watermark import (
    _WATERMARK_KEY,
    _compute_fingerprint,
    stamp,
    verify,
    remove,
    WatermarkResult,
)


@pytest.fixture()
def secrets() -> dict:
    return {"API_KEY": "abc123", "DB_PASS": "secret"}


def test_stamp_adds_watermark_key(secrets):
    stamp(secrets)
    assert _WATERMARK_KEY in secrets


def test_stamp_stores_label(secrets):
    stamp(secrets, label="prod-deploy")
    assert secrets[_WATERMARK_KEY]["label"] == "prod-deploy"


def test_stamp_stores_fingerprint_and_timestamp(secrets):
    stamp(secrets)
    entry = secrets[_WATERMARK_KEY]
    assert "fingerprint" in entry
    assert "timestamp" in entry
    assert isinstance(entry["fingerprint"], str)
    assert len(entry["fingerprint"]) == 64  # SHA-256 hex


def test_verify_returns_watermark_result_type(secrets):
    stamp(secrets)
    result = verify(secrets)
    assert isinstance(result, WatermarkResult)


def test_verify_valid_after_stamp(secrets):
    stamp(secrets, label="ci")
    result = verify(secrets)
    assert result.present is True
    assert result.valid is True
    assert result.label == "ci"


def test_verify_not_present_when_no_watermark(secrets):
    result = verify(secrets)
    assert result.present is False
    assert result.valid is False


def test_verify_invalid_after_tampering(secrets):
    stamp(secrets)
    secrets["EXTRA_KEY"] = "injected"  # tamper
    result = verify(secrets)
    assert result.present is True
    assert result.valid is False


def test_verify_invalid_after_fingerprint_mutation(secrets):
    stamp(secrets)
    secrets[_WATERMARK_KEY]["fingerprint"] = "deadbeef" * 8
    result = verify(secrets)
    assert result.valid is False


def test_remove_deletes_watermark_key(secrets):
    stamp(secrets)
    remove(secrets)
    assert _WATERMARK_KEY not in secrets


def test_remove_is_idempotent(secrets):
    remove(secrets)  # no watermark present — should not raise
    assert _WATERMARK_KEY not in secrets


def test_stamp_does_not_include_watermark_in_fingerprint(secrets):
    """Re-stamping should produce a consistent fingerprint over real secrets only."""
    stamp(secrets, label="v1")
    fp1 = secrets[_WATERMARK_KEY]["fingerprint"]
    ts1 = secrets[_WATERMARK_KEY]["timestamp"]
    # Recompute independently — internal key must be excluded
    expected = _compute_fingerprint(secrets, "v1", ts1)
    assert fp1 == expected


def test_different_labels_produce_different_fingerprints(secrets):
    import copy, time
    s1 = copy.deepcopy(secrets)
    s2 = copy.deepcopy(secrets)
    ts = time.time()
    fp1 = _compute_fingerprint(s1, "alpha", ts)
    fp2 = _compute_fingerprint(s2, "beta", ts)
    assert fp1 != fp2
