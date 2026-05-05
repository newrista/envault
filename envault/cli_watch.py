"""CLI commands for the watch feature."""

from __future__ import annotations

import click

from envault.audit import record_event
from envault.vault import Vault
from envault.watch import detect_changes, save_watch_state, _secret_fingerprint


@click.group("watch")
def watch_group() -> None:
    """Watch secrets for changes."""


@watch_group.command("snapshot")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def snapshot_cmd(vault_dir: str, password: str) -> None:
    """Record the current state of secrets as the watch baseline."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    save_watch_state(secrets, _secret_fingerprint(secrets))
    vault.save(secrets, password)
    record_event(vault_dir, "watch_snapshot", key="*")
    click.echo("Watch baseline recorded.")


@watch_group.command("check")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def check_cmd(vault_dir: str, password: str) -> None:
    """Show secrets that changed since the last watch snapshot."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    changes = detect_changes(secrets)

    if not changes:
        click.echo("No changes detected since last snapshot.")
        return

    for key, change_type in sorted(changes.items()):
        colour = {"added": "green", "removed": "red", "modified": "yellow"}.get(
            change_type, "white"
        )
        click.echo(click.style(f"  [{change_type.upper():8s}] {key}", fg=colour))

    record_event(vault_dir, "watch_check", key="*", detail=str(len(changes)))


@watch_group.command("reset")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def reset_cmd(vault_dir: str, password: str) -> None:
    """Clear the watch baseline (next check will report everything as added)."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    secrets.pop("__watch_state__", None)
    vault.save(secrets, password)
    record_event(vault_dir, "watch_reset", key="*")
    click.echo("Watch baseline cleared.")
