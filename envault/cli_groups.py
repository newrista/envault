"""CLI commands for managing secret groups."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.groups import (
    add_to_group,
    create_group,
    delete_group,
    get_group_keys,
    list_groups,
    remove_from_group,
)


@click.group("groups")
def groups_group() -> None:
    """Manage named groups of secrets."""


@groups_group.command("create")
@click.argument("vault_path")
@click.argument("group")
@click.password_option("--password", prompt=True, help="Vault password.")
def create_cmd(vault_path: str, group: str, password: str) -> None:
    """Create a new empty group inside VAULT_PATH."""
    vault = Vault(vault_path)
    secrets = vault.load(password)
    create_group(secrets, group)
    vault.save(secrets, password)
    click.echo(f"Group '{group}' created.")


@groups_group.command("delete")
@click.argument("vault_path")
@click.argument("group")
@click.password_option("--password", prompt=True, help="Vault password.")
def delete_cmd(vault_path: str, group: str, password: str) -> None:
    """Delete a group (secrets are NOT removed from the vault)."""
    vault = Vault(vault_path)
    secrets = vault.load(password)
    try:
        delete_group(secrets, group)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Group '{group}' deleted.")


@groups_group.command("add")
@click.argument("vault_path")
@click.argument("group")
@click.argument("key")
@click.password_option("--password", prompt=True, help="Vault password.")
def add_cmd(vault_path: str, group: str, key: str, password: str) -> None:
    """Add KEY to GROUP inside VAULT_PATH."""
    vault = Vault(vault_path)
    secrets = vault.load(password)
    try:
        add_to_group(secrets, group, key)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Key '{key}' added to group '{group}'.")


@groups_group.command("remove")
@click.argument("vault_path")
@click.argument("group")
@click.argument("key")
@click.password_option("--password", prompt=True, help="Vault password.")
def remove_cmd(vault_path: str, group: str, key: str, password: str) -> None:
    """Remove KEY from GROUP."""
    vault = Vault(vault_path)
    secrets = vault.load(password)
    try:
        remove_from_group(secrets, group, key)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Key '{key}' removed from group '{group}'.")


@groups_group.command("list")
@click.argument("vault_path")
@click.password_option("--password", prompt=True, help="Vault password.")
def list_cmd(vault_path: str, password: str) -> None:
    """List all groups in VAULT_PATH."""
    vault = Vault(vault_path)
    secrets = vault.load(password)
    groups = list_groups(secrets)
    if not groups:
        click.echo("No groups defined.")
    else:
        for g in groups:
            keys = get_group_keys(secrets, g)
            click.echo(f"{g} ({len(keys)} key(s)): {', '.join(keys) or '—'}")
