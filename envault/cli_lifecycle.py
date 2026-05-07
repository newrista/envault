"""CLI commands for secret lifecycle management."""

from __future__ import annotations

import click

from envault.lifecycle import (
    VALID_STATES,
    get_state,
    list_by_state,
    remove_state,
    set_state,
)
from envault.vault import Vault


@click.group(name="lifecycle")
def lifecycle_group():
    """Manage secret lifecycle states (active, deprecated, retired)."""


@lifecycle_group.command(name="set")
@click.argument("key")
@click.argument("state", type=click.Choice(VALID_STATES))
@click.option("--reason", default="", help="Reason for the state change.")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def set_cmd(key, state, reason, vault_dir, password):
    """Set the lifecycle STATE for KEY."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        set_state(secrets, key, state, reason)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Set '{key}' lifecycle state to '{state}'.")


@lifecycle_group.command(name="show")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def show_cmd(key, vault_dir, password):
    """Show lifecycle metadata for KEY."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    entry = get_state(secrets, key)
    if entry is None:
        click.echo(f"No lifecycle metadata for '{key}'.")
        return
    for field, value in entry.items():
        click.echo(f"  {field}: {value}")


@lifecycle_group.command(name="list")
@click.argument("state", type=click.Choice(VALID_STATES))
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def list_cmd(state, vault_dir, password):
    """List all keys in the given lifecycle STATE."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    keys = list_by_state(secrets, state)
    if not keys:
        click.echo(f"No keys in state '{state}'.")
        return
    for k in keys:
        click.echo(k)


@lifecycle_group.command(name="remove")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def remove_cmd(key, vault_dir, password):
    """Remove lifecycle metadata for KEY."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        remove_state(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Removed lifecycle metadata for '{key}'.")
