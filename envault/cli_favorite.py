"""CLI commands for managing favorite secrets."""
from __future__ import annotations

import click

from envault.vault import Vault
from envault.favorite import add_favorite, remove_favorite, is_favorite, list_favorites


@click.group("favorites")
def favorite_group() -> None:
    """Mark secrets as favorites for quick access."""


@favorite_group.command("add")
@click.argument("key")
@click.option("--note", default="", help="Optional short note for this favorite.")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def add_cmd(key: str, note: str, vault_dir: str, password: str) -> None:
    """Add KEY to favorites."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        add_favorite(secrets, key, note)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Added '{key}' to favorites.")


@favorite_group.command("remove")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def remove_cmd(key: str, vault_dir: str, password: str) -> None:
    """Remove KEY from favorites."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        remove_favorite(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Removed '{key}' from favorites.")


@favorite_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def list_cmd(vault_dir: str, password: str) -> None:
    """List all favorite secrets."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    favs = list_favorites(secrets)
    if not favs:
        click.echo("No favorites set.")
        return
    for entry in favs:
        note_part = f"  # {entry['note']}" if entry["note"] else ""
        click.echo(f"  {entry['key']}{note_part}")


@favorite_group.command("check")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def check_cmd(key: str, vault_dir: str, password: str) -> None:
    """Check whether KEY is a favorite."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    if is_favorite(secrets, key):
        click.echo(f"'{key}' is a favorite.")
    else:
        click.echo(f"'{key}' is NOT a favorite.")
