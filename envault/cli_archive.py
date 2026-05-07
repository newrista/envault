"""CLI commands for archiving and restoring secrets."""

import click
from envault.vault import Vault
from envault.archive import (
    archive_secret,
    restore_secret,
    list_archived,
    purge_archived,
    get_archived,
)


@click.group("archive")
def archive_group():
    """Soft-delete and restore secrets."""


@archive_group.command("add")
@click.argument("key")
@click.option("--reason", default="", help="Reason for archiving.")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def add_cmd(key, reason, vault_dir, password):
    """Archive (soft-delete) a secret."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        archive_secret(secrets, key, reason=reason)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    click.echo(f"Archived '{key}'.")


@archive_group.command("restore")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def restore_cmd(key, vault_dir, password):
    """Restore an archived secret to the active vault."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        restore_secret(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    click.echo(f"Restored '{key}'.")


@archive_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def list_cmd(vault_dir, password):
    """List all archived secrets."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    keys = list_archived(secrets)
    if not keys:
        click.echo("No archived secrets.")
        return
    for key in keys:
        meta = get_archived(secrets, key)
        reason = f" — {meta['reason']}" if meta.get("reason") else ""
        click.echo(f"{key}  (archived {meta['archived_at']}{reason})")


@archive_group.command("purge")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
@click.confirmation_option(prompt="Permanently delete this archived secret?")
def purge_cmd(key, vault_dir, password):
    """Permanently delete an archived secret."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        purge_archived(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    click.echo(f"Purged '{key}' from archive.")
