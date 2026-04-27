"""Tests for envault.snapshot."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envault.snapshot import (
    create_snapshot,
    list_snapshots,
    load_snapshot,
    delete_snapshot,
    SNAPSHOT_DIR_NAME,
)


@pytest.fixture()
def vault_dir(tmp_path: Path) -> Path:
    return tmp_path


SECRETS = {"DB_URL": "postgres://localhost/db", "API_KEY": "secret123"}


def test_create_snapshot_writes_file(vault_dir: Path) -> None:
    path = create_snapshot(vault_dir, SECRETS)
    assert path.exists()
    assert path.suffix == ".json"


def test_create_snapshot_contains_secrets(vault_dir: Path) -> None:
    path = create_snapshot(vault_dir, SECRETS, label="before_deploy")
    data = json.loads(path.read_text())
    assert data["secrets"] == SECRETS
    assert data["label"] == "before_deploy"
    assert isinstance(data["timestamp"], int)


def test_create_snapshot_label_in_filename(vault_dir: Path) -> None:
    path = create_snapshot(vault_dir, SECRETS, label="release v1")
    assert "release_v1" in path.name


def test_list_snapshots_empty(vault_dir: Path) -> None:
    assert list_snapshots(vault_dir) == []


def test_list_snapshots_returns_metadata(vault_dir: Path) -> None:
    create_snapshot(vault_dir, SECRETS, label="snap1")
    create_snapshot(vault_dir, {"X": "1"}, label="snap2")
    snaps = list_snapshots(vault_dir)
    assert len(snaps) == 2
    assert snaps[0]["key_count"] == 2
    assert snaps[1]["key_count"] == 1


def test_list_snapshots_sorted_oldest_first(vault_dir: Path) -> None:
    p1 = create_snapshot(vault_dir, SECRETS, label="first")
    p2 = create_snapshot(vault_dir, SECRETS, label="second")
    snaps = list_snapshots(vault_dir)
    names = [s["file"] for s in snaps]
    assert names.index(p1.name) < names.index(p2.name)


def test_load_snapshot_returns_secrets(vault_dir: Path) -> None:
    path = create_snapshot(vault_dir, SECRETS)
    loaded = load_snapshot(vault_dir, path.name)
    assert loaded == SECRETS


def test_load_snapshot_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_snapshot(vault_dir, "nonexistent.json")


def test_delete_snapshot_removes_file(vault_dir: Path) -> None:
    path = create_snapshot(vault_dir, SECRETS)
    delete_snapshot(vault_dir, path.name)
    assert not path.exists()
    assert list_snapshots(vault_dir) == []


def test_delete_snapshot_missing_raises(vault_dir: Path) -> None:
    with pytest.raises(FileNotFoundError):
        delete_snapshot(vault_dir, "ghost.json")


def test_snapshots_stored_in_subdirectory(vault_dir: Path) -> None:
    create_snapshot(vault_dir, SECRETS)
    snap_dir = vault_dir / SNAPSHOT_DIR_NAME
    assert snap_dir.is_dir()
    assert len(list(snap_dir.glob("*.json"))) == 1
