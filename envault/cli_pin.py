"""CLI commands for pin management."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.pin import pin_secret, unpin_secret, is_pinned, list_pinned


@click.group("pin")
def pin_group() -> None:
    """Pin secrets to prevent accidental rotation."""


@pin_group.command("add")
@click.argument("key")
@click.option("--reason", "-r", default="", help="Reason for pinning.")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def add_cmd(key: str, reason: str, vault_dir: str, password: str) -> None:
    """Pin KEY to its current value."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        pin_secret(secrets, key, reason)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Pinned '{key}'." + (f" Reason: {reason}" if reason else ""))


@pin_group.command("remove")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def remove_cmd(key: str, vault_dir: str, password: str) -> None:
    """Unpin KEY, allowing it to be rotated again."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        unpin_secret(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Unpinned '{key}'.")


@pin_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt="Vault password", hide_input=True)
def list_cmd(vault_dir: str, password: str) -> None:
    """List all pinned secrets."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    pinned = list_pinned(secrets)
    if not pinned:
        click.echo("No secrets are currently pinned.")
        return
    for key, reason in pinned.items():
        line = f"  {key}"
        if reason:
            line += f"  ({reason})"
        click.echo(line)


@pin_group.command("check")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt="Vault password", hide_input=True)
def check_cmd(key: str, vault_dir: str, password: str) -> None:
    """Check whether KEY is pinned."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    if is_pinned(secrets, key):
        click.echo(f"'{key}' is pinned.")
    else:
        click.echo(f"'{key}' is not pinned.")
