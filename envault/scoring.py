"""Vault health scoring — aggregate a numeric health score for a vault."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envault.ttl import is_expired, get_ttl
from envault.rotation import is_rotation_due
from envault.schema import get_schema
from envault.pin import is_pinned
from envault.readonly import _get_readonly_index

_INTERNAL_PREFIX = "__"


@dataclass
class ScoreReport:
    total_keys: int = 0
    expired_count: int = 0
    stale_count: int = 0
    no_schema_count: int = 0
    score: float = 100.0
    breakdown: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> str:
        grade = (
            "A" if self.score >= 90
            else "B" if self.score >= 75
            else "C" if self.score >= 60
            else "D" if self.score >= 40
            else "F"
        )
        return (
            f"Health score: {self.score:.1f}/100 (Grade {grade}) "
            f"| keys={self.total_keys} expired={self.expired_count} "
            f"stale={self.stale_count} no_schema={self.no_schema_count}"
        )


def score_vault(secrets: dict[str, str]) -> ScoreReport:
    """Compute a 0-100 health score for *secrets*.

    Penalties (applied to the 100-point base):
      - Each expired TTL:       -10 pts
      - Each stale rotation:    -5 pts
      - Each key lacking schema: -2 pts  (capped at 20 pts total)
    """
    user_keys = [
        k for k in secrets if not k.startswith(_INTERNAL_PREFIX)
    ]
    total = len(user_keys)
    if total == 0:
        return ScoreReport()

    expired = sum(1 for k in user_keys if is_expired(secrets, k))
    stale = sum(
        1 for k in user_keys
        if not is_expired(secrets, k) and is_rotation_due(secrets, k)
    )
    no_schema = sum(
        1 for k in user_keys if get_schema(secrets, k) is None
    )

    penalty = expired * 10 + stale * 5 + min(no_schema * 2, 20)
    score = max(0.0, 100.0 - penalty)

    return ScoreReport(
        total_keys=total,
        expired_count=expired,
        stale_count=stale,
        no_schema_count=no_schema,
        score=score,
        breakdown={
            "expired_penalty": expired * 10,
            "stale_penalty": stale * 5,
            "no_schema_penalty": min(no_schema * 2, 20),
        },
    )
