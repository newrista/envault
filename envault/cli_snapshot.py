"""CLI commands for vault snapshots."""

from __future__ import annotations

import click
from pathlib import Path
from datetime import datetime

from envault.snapshot import (
    create_snapshot,
    list_snapshots,
    load_snapshot,
    delete_snapshot,
)
from envault.vault import Vault


@click.group("snapshot")
def snapshot_group() -> None:
    """Manage vault snapshots."""


@snapshot_group.command("create")
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--label", default=None, help="Optional label for the snapshot.")
def create_cmd(vault_dir: str, password: str, label: str | None) -> None:
    """Create a snapshot of the current vault state."""
    vdir = Path(vault_dir)
    vault = Vault(vdir, password)
    secrets = vault.load()
    path = create_snapshot(vdir, secrets, label=label)
    click.echo(f"Snapshot created: {path.name}")


@snapshot_group.command("list")
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
def list_cmd(vault_dir: str) -> None:
    """List all available snapshots."""
    snaps = list_snapshots(Path(vault_dir))
    if not snaps:
        click.echo("No snapshots found.")
        return
    for s in snaps:
        dt = datetime.fromtimestamp(s["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        label = f"  [{s['label']}]" if s["label"] else ""
        click.echo(f"{s['file']}  {dt}  {s['key_count']} keys{label}")


@snapshot_group.command("restore")
@click.argument("filename")
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.confirmation_option(prompt="This will overwrite the current vault. Continue?")
def restore_cmd(filename: str, vault_dir: str, password: str) -> None:
    """Restore vault secrets from a snapshot."""
    vdir = Path(vault_dir)
    secrets = load_snapshot(vdir, filename)
    vault = Vault(vdir, password)
    vault.save(secrets)
    click.echo(f"Vault restored from {filename} ({len(secrets)} keys).")


@snapshot_group.command("delete")
@click.argument("filename")
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
@click.confirmation_option(prompt="Delete this snapshot?")
def delete_cmd(filename: str, vault_dir: str) -> None:
    """Delete a snapshot."""
    delete_snapshot(Path(vault_dir), filename)
    click.echo(f"Snapshot {filename} deleted.")
