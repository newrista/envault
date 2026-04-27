"""CLI commands for managing secret tags."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.tags import add_tag, remove_tag, get_tags, list_by_tag, all_tags


@click.group("tags")
def tags_group() -> None:
    """Manage tags on secrets."""


@tags_group.command("add")
@click.argument("vault_name")
@click.argument("key")
@click.argument("tag")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def add_cmd(vault_name: str, key: str, tag: str, password: str) -> None:
    """Add TAG to KEY in VAULT_NAME."""
    vault = Vault(vault_name)
    secrets = vault.load(password)
    try:
        add_tag(secrets, key, tag)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Tag '{tag}' added to '{key}'.")


@tags_group.command("remove")
@click.argument("vault_name")
@click.argument("key")
@click.argument("tag")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def remove_cmd(vault_name: str, key: str, tag: str, password: str) -> None:
    """Remove TAG from KEY in VAULT_NAME."""
    vault = Vault(vault_name)
    secrets = vault.load(password)
    remove_tag(secrets, key, tag)
    vault.save(secrets, password)
    click.echo(f"Tag '{tag}' removed from '{key}'.")


@tags_group.command("list")
@click.argument("vault_name")
@click.option("--tag", default=None, help="Filter secrets by this tag.")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def list_cmd(vault_name: str, tag: str | None, password: str) -> None:
    """List tags for all secrets, or filter by TAG."""
    vault = Vault(vault_name)
    secrets = vault.load(password)
    if tag:
        keys = list_by_tag(secrets, tag)
        if not keys:
            click.echo(f"No secrets found with tag '{tag}'.")
        else:
            for k in keys:
                click.echo(k)
    else:
        index = all_tags(secrets)
        if not index:
            click.echo("No tags defined.")
        else:
            for k, tags in sorted(index.items()):
                click.echo(f"{k}: {', '.join(tags)}")


@tags_group.command("show")
@click.argument("vault_name")
@click.argument("key")
@click.password_option(prompt="Vault password", confirmation_prompt=False)
def show_cmd(vault_name: str, key: str, password: str) -> None:
    """Show tags for a specific KEY."""
    vault = Vault(vault_name)
    secrets = vault.load(password)
    tags = get_tags(secrets, key)
    if not tags:
        click.echo(f"'{key}' has no tags.")
    else:
        click.echo(", ".join(tags))
