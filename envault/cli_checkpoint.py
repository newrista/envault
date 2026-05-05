"""CLI commands for vault checkpoints."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.checkpoint import (
    create_checkpoint,
    delete_checkpoint,
    get_checkpoint,
    list_checkpoints,
    diff_from_checkpoint,
)


@click.group("checkpoint")
def checkpoint_group():
    """Manage named vault checkpoints."""


@checkpoint_group.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Optional description.")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def create_cmd(name, description, vault_dir, password):
    """Create a named checkpoint of the current vault state."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    meta = create_checkpoint(secrets, name, description)
    vault.save(secrets)
    click.echo(f"Checkpoint '{name}' created at {meta['created_at']:.0f} with {len(meta['keys'])} keys.")


@checkpoint_group.command("delete")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def delete_cmd(name, vault_dir, password):
    """Delete a named checkpoint."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    delete_checkpoint(secrets, name)
    vault.save(secrets)
    click.echo(f"Checkpoint '{name}' deleted.")


@checkpoint_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def list_cmd(vault_dir, password):
    """List all checkpoints."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    checkpoints = list_checkpoints(secrets)
    if not checkpoints:
        click.echo("No checkpoints found.")
        return
    for cp in checkpoints:
        desc = f" — {cp['description']}" if cp["description"] else ""
        click.echo(f"  {cp['name']}: {len(cp['keys'])} keys{desc}")


@checkpoint_group.command("diff")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt=True, confirmation_prompt=False)
def diff_cmd(name, vault_dir, password):
    """Show keys added/removed since a checkpoint."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    result = diff_from_checkpoint(secrets, name)
    if result["added"]:
        click.echo("Added:")
        for k in result["added"]:
            click.echo(f"  + {k}")
    if result["removed"]:
        click.echo("Removed:")
        for k in result["removed"]:
            click.echo(f"  - {k}")
    if not result["added"] and not result["removed"]:
        click.echo("No changes since checkpoint.")
