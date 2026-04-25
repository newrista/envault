"""CLI entry point for envault vault management commands."""

import click
import getpass

from envault.vault import Vault


@click.group()
def cli():
    """envault — secure environment variable vault manager."""


@cli.command("init")
@click.argument("project")
def init_vault(project: str):
    """Initialize a new empty vault for PROJECT."""
    vault = Vault(project)
    if vault.exists():
        click.echo(f"Vault '{project}' already exists.")
        return
    password = getpass.getpass("Set vault password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        click.echo("Passwords do not match.", err=True)
        raise SystemExit(1)
    vault.save({}, password)
    click.echo(f"Vault '{project}' created at {vault.path}")


@cli.command("set")
@click.argument("project")
@click.argument("key")
@click.argument("value")
def set_secret(project: str, key: str, value: str):
    """Set KEY=VALUE in PROJECT vault."""
    vault = Vault(project)
    password = getpass.getpass("Vault password: ")
    secrets = vault.load(password) if vault.exists() else {}
    secrets[key] = value
    vault.save(secrets, password)
    click.echo(f"Set '{key}' in vault '{project}'.")


@cli.command("get")
@click.argument("project")
@click.argument("key")
def get_secret(project: str, key: str):
    """Get the value of KEY from PROJECT vault."""
    vault = Vault(project)
    password = getpass.getpass("Vault password: ")
    secrets = vault.load(password)
    if key not in secrets:
        click.echo(f"Key '{key}' not found.", err=True)
        raise SystemExit(1)
    click.echo(secrets[key])


@cli.command("list")
def list_vaults():
    """List all available vaults."""
    vaults = Vault.list_vaults()
    if not vaults:
        click.echo("No vaults found.")
    for name in vaults:
        click.echo(name)


if __name__ == "__main__":
    cli()
