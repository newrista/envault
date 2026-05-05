"""Lint secrets against defined schemas, TTLs, tags, and notes for hygiene issues."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envault.schema import get_schema, validate_value
from envault.ttl import get_ttl, is_expired
from envault.tags import get_tags
from envault.notes import get_note

_INTERNAL_PREFIX = "__"


@dataclass
class LintIssue:
    key: str
    level: str  # "error" | "warning" | "info"
    message: str


@dataclass
class LintReport:
    issues: list[LintIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[LintIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> list[LintIssue]:
        return [i for i in self.issues if i.level == "warning"]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def summary(self) -> str:
        return (
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s), "
            f"{len(self.issues) - len(self.errors) - len(self.warnings)} info(s)"
        )


def lint_secrets(
    secrets: dict[str, Any],
    *,
    check_schema: bool = True,
    check_ttl: bool = True,
    check_tags: bool = True,
    check_notes: bool = False,
) -> LintReport:
    """Run lint checks on all non-internal secrets and return a LintReport."""
    report = LintReport()

    for key, value in secrets.items():
        if key.startswith(_INTERNAL_PREFIX):
            continue

        if check_schema:
            schema = get_schema(secrets, key)
            if schema:
                try:
                    validate_value(key, value, schema)
                except Exception as exc:  # SchemaValidationError
                    report.issues.append(LintIssue(key, "error", str(exc)))
            else:
                report.issues.append(
                    LintIssue(key, "info", f"'{key}' has no schema defined")
                )

        if check_ttl:
            ttl_entry = get_ttl(secrets, key)
            if ttl_entry is None:
                report.issues.append(
                    LintIssue(key, "warning", f"'{key}' has no TTL set")
                )
            elif is_expired(secrets, key):
                report.issues.append(
                    LintIssue(key, "error", f"'{key}' TTL has expired")
                )

        if check_tags:
            tags = get_tags(secrets, key)
            if not tags:
                report.issues.append(
                    LintIssue(key, "info", f"'{key}' has no tags")
                )

        if check_notes:
            note = get_note(secrets, key)
            if not note:
                report.issues.append(
                    LintIssue(key, "info", f"'{key}' has no note/description")
                )

    return report
