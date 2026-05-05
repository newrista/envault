"""Verify vault secrets against their schemas and TTL/pin constraints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envault.schema import get_schema, validate_value, SchemaValidationError
from envault.ttl import is_expired, get_ttl
from envault.pin import is_pinned


@dataclass
class VerifyIssue:
    key: str
    level: str  # 'error' | 'warning' | 'info'
    message: str


@dataclass
class VerifyReport:
    issues: list[VerifyIssue] = field(default_factory=list)

    def errors(self) -> list[VerifyIssue]:
        return [i for i in self.issues if i.level == "error"]

    def warnings(self) -> list[VerifyIssue]:
        return [i for i in self.issues if i.level == "warning"]

    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    def summary(self) -> str:
        e = len(self.errors())
        w = len(self.warnings())
        return f"{e} error(s), {w} warning(s)"


def verify_secrets(secrets: dict[str, Any]) -> VerifyReport:
    """Run all verification checks on the provided secrets dict."""
    report = VerifyReport()
    internal_prefix = "__"

    for key, value in secrets.items():
        if key.startswith(internal_prefix):
            continue

        # Schema validation
        schema = get_schema(secrets, key)
        if schema:
            try:
                validate_value(key, value, schema)
            except SchemaValidationError as exc:
                report.issues.append(VerifyIssue(key=key, level="error", message=str(exc)))
        else:
            report.issues.append(
                VerifyIssue(key=key, level="info", message="No schema defined for key.")
            )

        # TTL expiry check
        if is_expired(secrets, key):
            ttl_info = get_ttl(secrets, key)
            report.issues.append(
                VerifyIssue(
                    key=key,
                    level="warning",
                    message=f"Secret has expired (TTL: {ttl_info}).",
                )
            )

        # Pinned secret with no value guard
        if is_pinned(secrets, key) and (value is None or value == ""):
            report.issues.append(
                VerifyIssue(
                    key=key,
                    level="error",
                    message="Pinned secret has an empty or null value.",
                )
            )

    return report
