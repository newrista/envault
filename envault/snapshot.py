"""Snapshot support: capture and restore vault state at a point in time."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

SNAPSHOT_DIR_NAME = ".snapshots"


def _snapshot_dir(vault_dir: Path) -> Path:
    d = vault_dir / SNAPSHOT_DIR_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


def create_snapshot(vault_dir: Path, secrets: Dict[str, str], label: Optional[str] = None) -> Path:
    """Persist a snapshot of *secrets* inside *vault_dir*.

    Returns the path of the written snapshot file.
    """
    ts = int(time.time())
    slug = label.replace(" ", "_") if label else "snap"
    filename = f"{ts}_{slug}.json"
    snapshot_path = _snapshot_dir(vault_dir) / filename
    payload = {
        "timestamp": ts,
        "label": label or "",
        "secrets": secrets,
    }
    snapshot_path.write_text(json.dumps(payload, indent=2))
    return snapshot_path


def list_snapshots(vault_dir: Path) -> List[Dict]:
    """Return metadata for all snapshots, sorted oldest-first."""
    snap_dir = _snapshot_dir(vault_dir)
    results = []
    for p in sorted(snap_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            results.append({
                "file": p.name,
                "timestamp": data.get("timestamp", 0),
                "label": data.get("label", ""),
                "key_count": len(data.get("secrets", {})),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return results


def load_snapshot(vault_dir: Path, filename: str) -> Dict[str, str]:
    """Load and return the secrets dict from a snapshot file."""
    snap_path = _snapshot_dir(vault_dir) / filename
    if not snap_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {filename}")
    data = json.loads(snap_path.read_text())
    return data["secrets"]


def delete_snapshot(vault_dir: Path, filename: str) -> None:
    """Delete a snapshot by filename."""
    snap_path = _snapshot_dir(vault_dir) / filename
    if not snap_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {filename}")
    snap_path.unlink()
