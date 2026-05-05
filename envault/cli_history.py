"""CLI commands for inspecting secret value history."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.history import get_history, clear_history, list_keys_with_history


@click.group("history")
def history_group() -> None:
    """View and manage secret value history."""


@history_group.command("show")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--limit", default=10, show_default=True, help="Max entries to display.")
def show_cmd(key: str, vault_dir: str, password: str, limit: int) -> None:
    """Show previous values for KEY."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        entries = get_history(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    if not entries:
        click.echo(f"No history recorded for '{key}'.")
        return

    click.echo(f"History for '{key}' (most recent last):")
    for entry in entries[-limit:]:
        click.echo(f"  [{entry['recorded_at']}]  {entry['value']}")


@history_group.command("clear")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.confirmation_option(prompt="Clear all history for this key?")
def clear_cmd(key: str, vault_dir: str, password: str) -> None:
    """Delete all history entries for KEY."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        clear_history(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"History cleared for '{key}'.")


@history_group.command("list")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def list_cmd(vault_dir: str, password: str) -> None:
    """List all keys that have recorded history."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    keys = list_keys_with_history(secrets)
    if not keys:
        click.echo("No history recorded for any key.")
        return
    for key in sorted(keys):
        click.echo(key)
