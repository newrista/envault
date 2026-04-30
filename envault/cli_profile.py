"""CLI commands for managing vault profiles."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.profile import (
    create_profile,
    delete_profile,
    add_key_to_profile,
    remove_key_from_profile,
    get_profile_keys,
    list_profiles,
    resolve_profile,
)


@click.group("profile")
def profile_group() -> None:
    """Manage named key profiles for environment-specific exports."""


@profile_group.command("create")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option(prompt="Vault password")
def create_cmd(name: str, vault_dir: str, password: str) -> None:
    """Create a new empty profile."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        create_profile(secrets, name)
        v.save(secrets, password)
        click.echo(f"Profile '{name}' created.")
    except Exception as exc:  # pragma: no cover
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("delete")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option(prompt="Vault password")
def delete_cmd(name: str, vault_dir: str, password: str) -> None:
    """Delete a profile."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        delete_profile(secrets, name)
        v.save(secrets, password)
        click.echo(f"Profile '{name}' deleted.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("add")
@click.argument("name")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option(prompt="Vault password")
def add_cmd(name: str, key: str, vault_dir: str, password: str) -> None:
    """Add a key to a profile."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        add_key_to_profile(secrets, name, key)
        v.save(secrets, password)
        click.echo(f"Key '{key}' added to profile '{name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("remove")
@click.argument("name")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option(prompt="Vault password")
def remove_cmd(name: str, key: str, vault_dir: str, password: str) -> None:
    """Remove a key from a profile."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        remove_key_from_profile(secrets, name, key)
        v.save(secrets, password)
        click.echo(f"Key '{key}' removed from profile '{name}'.")
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@profile_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option(prompt="Vault password")
def list_cmd(vault_dir: str, password: str) -> None:
    """List all profiles."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    names = list_profiles(secrets)
    if not names:
        click.echo("No profiles defined.")
    else:
        for n in names:
            click.echo(n)


@profile_group.command("show")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--reveal", is_flag=True, default=False, help="Show secret values.")
@click.password_option(prompt="Vault password")
def show_cmd(name: str, vault_dir: str, reveal: bool, password: str) -> None:
    """Show keys (and optionally values) in a profile."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        if reveal:
            resolved = resolve_profile(secrets, name)
            for k, val in resolved.items():
                click.echo(f"{k}={val}")
        else:
            keys = get_profile_keys(secrets, name)
            if not keys:
                click.echo(f"Profile '{name}' is empty.")
            else:
                for k in keys:
                    click.echo(k)
    except KeyError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
