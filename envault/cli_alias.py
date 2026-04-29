"""CLI commands for managing secret key aliases."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.alias import add_alias, remove_alias, list_aliases, resolve_alias


@click.group("alias")
def alias_group() -> None:
    """Manage aliases for secret keys."""


@alias_group.command("add")
@click.argument("alias")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True)
def add_cmd(alias: str, key: str, vault_dir: str, password: str) -> None:
    """Add ALIAS pointing to KEY."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    try:
        add_alias(secrets, alias, key)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets)
    click.echo(f"Alias '{alias}' -> '{key}' added.")


@alias_group.command("remove")
@click.argument("alias")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True)
def remove_cmd(alias: str, vault_dir: str, password: str) -> None:
    """Remove ALIAS."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    try:
        remove_alias(secrets, alias)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets)
    click.echo(f"Alias '{alias}' removed.")


@alias_group.command("list")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True)
def list_cmd(vault_dir: str, password: str) -> None:
    """List all aliases."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    aliases = list_aliases(secrets)
    if not aliases:
        click.echo("No aliases defined.")
        return
    for alias, key in sorted(aliases.items()):
        click.echo(f"  {alias} -> {key}")


@alias_group.command("show")
@click.argument("alias")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True)
def show_cmd(alias: str, vault_dir: str, password: str) -> None:
    """Show the canonical key that ALIAS resolves to."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    canonical = resolve_alias(secrets, alias)
    if canonical is None:
        raise click.ClickException(f"No alias named '{alias}' found.")
    click.echo(canonical)
