"""Diff utilities for comparing vault secrets across snapshots or versions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class DiffResult:
    added: Dict[str, str] = field(default_factory=dict)
    removed: Dict[str, str] = field(default_factory=dict)
    changed: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    unchanged: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No changes detected."
        return ", ".join(parts)


def diff_secrets(
    old: Dict[str, str],
    new: Dict[str, str],
    show_values: bool = False,
) -> DiffResult:
    """Compare two secret dictionaries and return a DiffResult.

    Args:
        old: The baseline secrets mapping.
        new: The updated secrets mapping.
        show_values: If False, changed values are masked with '***'.

    Returns:
        A DiffResult describing additions, removals, changes, and unchanged keys.
    """
    result = DiffResult()
    all_keys = set(old) | set(new)

    for key in sorted(all_keys):
        if key not in old:
            result.added[key] = new[key] if show_values else "***"
        elif key not in new:
            result.removed[key] = old[key] if show_values else "***"
        elif old[key] != new[key]:
            if show_values:
                result.changed[key] = (old[key], new[key])
            else:
                result.changed[key] = ("***", "***")
        else:
            result.unchanged[key] = old[key] if show_values else "***"

    return result


def format_diff(result: DiffResult, show_values: bool = False) -> List[str]:
    """Render a DiffResult as a list of human-readable lines."""
    lines: List[str] = []
    for key, val in result.added.items():
        lines.append(f"  [+] {key}" + (f" = {val}" if show_values else ""))
    for key, val in result.removed.items():
        lines.append(f"  [-] {key}" + (f" = {val}" if show_values else ""))
    for key, (old_val, new_val) in result.changed.items():
        if show_values:
            lines.append(f"  [~] {key}: {old_val!r} -> {new_val!r}")
        else:
            lines.append(f"  [~] {key}")
    return lines
