"""Audit log for tracking secret access and mutations in envault vaults."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_LOG_FILENAME = ".envault_audit.jsonl"


def _audit_log_path(vault_dir: str) -> Path:
    return Path(vault_dir) / AUDIT_LOG_FILENAME


def record_event(
    vault_dir: str,
    action: str,
    key: str,
    actor: Optional[str] = None,
    note: Optional[str] = None,
) -> None:
    """Append a single audit event to the vault's audit log."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "key": key,
        "actor": actor or os.environ.get("USER", "unknown"),
        "note": note,
    }
    log_path = _audit_log_path(vault_dir)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")


def read_events(vault_dir: str) -> List[dict]:
    """Return all audit events for a vault, oldest first."""
    log_path = _audit_log_path(vault_dir)
    if not log_path.exists():
        return []
    events = []
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def filter_events(
    events: List[dict],
    action: Optional[str] = None,
    key: Optional[str] = None,
) -> List[dict]:
    """Filter audit events by action and/or key name."""
    result = events
    if action:
        result = [e for e in result if e.get("action") == action]
    if key:
        result = [e for e in result if e.get("key") == key]
    return result
