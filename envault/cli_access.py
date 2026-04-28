"""CLI commands for managing vault access policies."""

from __future__ import annotations

import click
from envault.vault import Vault
from envault import access as acc


@click.group(name="access")
def access_group() -> None:
    """Manage read/write permissions for vault secrets."""


@access_group.command("set")
@click.argument("key")
@click.argument("perms", nargs=-1, required=True)
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def set_cmd(key: str, perms: tuple, vault_dir: str, password: str) -> None:
    """Set permissions (read/write/deny) for KEY."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    try:
        acc.set_permission(secrets, key, list(perms))
    except ValueError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets)
    click.echo(f"Permissions for '{key}' set to: {', '.join(perms)}")


@access_group.command("get")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def get_cmd(key: str, vault_dir: str, password: str) -> None:
    """Show effective permissions for KEY."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    perms = acc.get_permission(secrets, key)
    click.echo(f"{key}: {', '.join(perms)}")


@access_group.command("remove")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def remove_cmd(key: str, vault_dir: str, password: str) -> None:
    """Remove the explicit permission rule for KEY."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    removed = acc.remove_permission(secrets, key)
    if removed:
        vault.save(secrets)
        click.echo(f"Permission rule for '{key}' removed.")
    else:
        click.echo(f"No explicit rule found for '{key}'.")


@access_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def list_cmd(vault_dir: str, password: str) -> None:
    """List all explicit permission rules in the vault."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    rules = acc.list_permissions(secrets)
    if not rules:
        click.echo("No explicit permission rules defined.")
        return
    for key, perms in sorted(rules.items()):
        click.echo(f"  {key}: {', '.join(perms)}")
