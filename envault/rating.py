"""Secret strength rating module for envault."""
from __future__ import annotations

import math
import re
from typing import Dict, List

# Internal prefix used by envault metadata keys
_INTERNAL_PREFIX = "__envault_"


class RatingResult:
    """Holds the rating details for a single secret value."""

    def __init__(self, key: str, score: int, grade: str, reasons: List[str]):
        self.key = key
        self.score = score
        self.grade = grade
        self.reasons = reasons

    def __repr__(self) -> str:  # pragma: no cover
        return f"RatingResult(key={self.key!r}, score={self.score}, grade={self.grade!r})"


def _entropy_bits(value: str) -> float:
    """Estimate Shannon entropy of *value* in bits."""
    if not value:
        return 0.0
    freq = {}
    for ch in value:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(value)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def rate_secret(key: str, value: str) -> RatingResult:
    """Rate a single secret value and return a RatingResult.

    Scoring rubric (max 100):
      - Length          up to 40 pts
      - Entropy         up to 40 pts
      - Charset variety up to 20 pts
    """
    reasons: List[str] = []
    score = 0

    # Length score (40 pts)
    length = len(value)
    length_score = min(40, int(length / 32 * 40))
    score += length_score
    if length < 8:
        reasons.append("Value is very short (< 8 chars)")
    elif length < 16:
        reasons.append("Value is short (< 16 chars)")

    # Entropy score (40 pts)
    entropy = _entropy_bits(value)
    entropy_score = min(40, int(entropy / 4.0 * 40))
    score += entropy_score
    if entropy < 2.0:
        reasons.append("Low entropy — value may be predictable")

    # Charset variety (20 pts)
    has_lower = bool(re.search(r'[a-z]', value))
    has_upper = bool(re.search(r'[A-Z]', value))
    has_digit = bool(re.search(r'\d', value))
    has_special = bool(re.search(r'[^a-zA-Z0-9]', value))
    variety = sum([has_lower, has_upper, has_digit, has_special])
    variety_score = int(variety / 4 * 20)
    score += variety_score
    if not has_upper:
        reasons.append("No uppercase letters")
    if not has_digit:
        reasons.append("No digits")
    if not has_special:
        reasons.append("No special characters")

    # Grade
    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 30:
        grade = "D"
    else:
        grade = "F"

    return RatingResult(key=key, score=score, grade=grade, reasons=reasons)


def rate_all(secrets: Dict[str, str]) -> List[RatingResult]:
    """Rate every non-internal secret in *secrets*."""
    results = []
    for key, value in secrets.items():
        if key.startswith(_INTERNAL_PREFIX):
            continue
        results.append(rate_secret(key, value))
    return results


def summary(results: List[RatingResult]) -> Dict[str, int]:
    """Return a grade-frequency mapping for a list of RatingResults."""
    counts: Dict[str, int] = {g: 0 for g in ("A", "B", "C", "D", "F")}
    for r in results:
        counts[r.grade] += 1
    return counts
