"""Tests for envault.rating."""
import pytest
from envault.rating import (
    RatingResult,
    _entropy_bits,
    rate_secret,
    rate_all,
    summary,
)


# ---------------------------------------------------------------------------
# _entropy_bits
# ---------------------------------------------------------------------------

def test_entropy_empty_string_is_zero():
    assert _entropy_bits("") == 0.0


def test_entropy_single_char_is_zero():
    assert _entropy_bits("aaaa") == 0.0


def test_entropy_two_equal_chars_is_one():
    result = _entropy_bits("ab")
    assert abs(result - 1.0) < 1e-9


def test_entropy_increases_with_variety():
    low = _entropy_bits("aaabbb")
    high = _entropy_bits("abcdef")
    assert high > low


# ---------------------------------------------------------------------------
# rate_secret
# ---------------------------------------------------------------------------

def test_rate_secret_returns_rating_result():
    result = rate_secret("MY_KEY", "s3cret!Value#99")
    assert isinstance(result, RatingResult)


def test_rate_secret_key_stored():
    result = rate_secret("API_KEY", "abc")
    assert result.key == "API_KEY"


def test_rate_secret_short_value_gets_low_score():
    result = rate_secret("K", "abc")
    assert result.score < 50
    assert result.grade in ("D", "F")


def test_rate_secret_strong_value_gets_high_score():
    strong = "Tr0ub4dor&3_xYz!9Qm@2024"
    result = rate_secret("TOKEN", strong)
    assert result.score >= 70
    assert result.grade in ("A", "B")


def test_rate_secret_all_lowercase_reason():
    result = rate_secret("PW", "alllowercase")
    reasons_text = " ".join(result.reasons)
    assert "uppercase" in reasons_text.lower()


def test_rate_secret_no_digit_reason():
    result = rate_secret("PW", "NoDigitsHere!")
    reasons_text = " ".join(result.reasons)
    assert "digit" in reasons_text.lower()


def test_rate_secret_no_special_reason():
    result = rate_secret("PW", "NoSpecial1234")
    reasons_text = " ".join(result.reasons)
    assert "special" in reasons_text.lower()


def test_rate_secret_grade_f_for_empty():
    result = rate_secret("EMPTY", "")
    assert result.grade == "F"
    assert result.score == 0


def test_rate_secret_score_bounded_0_to_100():
    for val in ("", "a", "A1!x" * 20, "x" * 100):
        r = rate_secret("K", val)
        assert 0 <= r.score <= 100


# ---------------------------------------------------------------------------
# rate_all
# ---------------------------------------------------------------------------

def test_rate_all_skips_internal_keys():
    secrets = {
        "API_KEY": "abc123",
        "__envault_meta": "internal",
    }
    results = rate_all(secrets)
    keys = [r.key for r in results]
    assert "API_KEY" in keys
    assert "__envault_meta" not in keys


def test_rate_all_returns_one_result_per_user_key():
    secrets = {"A": "val1", "B": "val2", "__envault_x": "skip"}
    results = rate_all(secrets)
    assert len(results) == 2


# ---------------------------------------------------------------------------
# summary
# ---------------------------------------------------------------------------

def test_summary_all_grades_present():
    results = [
        RatingResult("a", 90, "A", []),
        RatingResult("b", 72, "B", []),
        RatingResult("c", 55, "C", []),
    ]
    counts = summary(results)
    assert counts["A"] == 1
    assert counts["B"] == 1
    assert counts["C"] == 1
    assert counts["D"] == 0
    assert counts["F"] == 0


def test_summary_empty_results():
    counts = summary([])
    assert sum(counts.values()) == 0
