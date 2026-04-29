"""Main CLI entry point for envault."""

import click
from pathlib import Path
from envault.vault import Vault
from envault.cli_audit import audit_group
from envault.cli_diff import diff_group
from envault.cli_snapshot import snapshot_group
from envault.cli_tags import tags_group
from envault.cli_access import access_group
from envault.cli_export import export_group
from envault.cli_alias import alias_group
from envault.cli_groups import groups_group
from envault.cli_hooks import hooks_group


@click.group()
def cli():
    """envault — Secure environment variable manager."""


@cli.command()
@click.option("--vault-dir", default=".", help="Directory for the vault.")
@click.password_option()
def init_vault(vault_dir, password):
    """Initialise a new vault."""
    vault = Vault(Path(vault_dir), password)
    if vault.exists():
        raise click.ClickException("Vault already exists.")
    vault.save({})
    click.echo("Vault initialised.")


@cli.command()
@click.argument("key")
@click.argument("value")
@click.option("--vault-dir", default=".", help="Directory for the vault.")
@click.option("--password", prompt=True, hide_input=True)
def set_secret(key, value, vault_dir, password):
    """Set a secret KEY to VALUE."""
    vault = Vault(Path(vault_dir), password)
    secrets = vault.load()
    secrets[key] = value
    vault.save(secrets)
    click.echo(f"Set {key}.")


@cli.command()
@click.argument("key")
@click.option("--vault-dir", default=".", help="Directory for the vault.")
@click.option("--password", prompt=True, hide_input=True)
def get_secret(key, vault_dir, password):
    """Get the value of secret KEY."""
    vault = Vault(Path(vault_dir), password)
    secrets = vault.load()
    if key not in secrets:
        raise click.ClickException(f"Key '{key}' not found.")
    click.echo(secrets[key])


@cli.command()
@click.option("--vault-dir", default=".", help="Directory for the vault.")
@click.option("--password", prompt=True, hide_input=True)
def list_secrets(vault_dir, password):
    """List all secret keys in the vault."""
    vault = Vault(Path(vault_dir), password)
    secrets = vault.load()
    for key in sorted(secrets):
        click.echo(key)


@cli.command()
@click.argument("key")
@click.option("--vault-dir", default=".", help="Directory for the vault.")
@click.option("--password", prompt=True, hide_input=True)
def delete_secret(key, vault_dir, password):
    """Delete secret KEY from the vault."""
    vault = Vault(Path(vault_dir), password)
    secrets = vault.load()
    if key not in secrets:
        raise click.ClickException(f"Key '{key}' not found.")
    del secrets[key]
    vault.save(secrets)
    click.echo(f"Deleted {key}.")


cli.add_command(audit_group, "audit")
cli.add_command(diff_group, "diff")
cli.add_command(snapshot_group, "snapshot")
cli.add_command(tags_group, "tags")
cli.add_command(access_group, "access")
cli.add_command(export_group, "export")
cli.add_command(alias_group, "alias")
cli.add_command(groups_group, "groups")
cli.add_command(hooks_group, "hooks")

if __name__ == "__main__":
    cli()
