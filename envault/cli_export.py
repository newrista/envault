"""CLI commands for exporting vault secrets to various formats."""

import click
from pathlib import Path

from .vault import Vault
from .export import export_secrets
from .audit import record_event


@click.group(name="export")
def export_group():
    """Export secrets from a vault to various formats."""
    pass


@export_group.command(name="dotenv")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Output file path. Defaults to stdout.",
)
@click.option("--keys", "-k", multiple=True, help="Specific keys to export (repeatable).")
def export_dotenv(vault_name: str, password: str, output: str, keys: tuple):
    """Export secrets as a .env file."""
    vault = Vault(vault_name)
    if not vault.exists():
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")

    secrets = vault.load(password)
    filter_keys = list(keys) if keys else None

    content = export_secrets(secrets, fmt="dotenv", keys=filter_keys)

    if output:
        Path(output).write_text(content)
        click.echo(f"Exported to {output}")
    else:
        click.echo(content, nl=False)

    record_event(vault_name, "export", {"format": "dotenv", "output": output or "<stdout>"})


@export_group.command(name="json")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Output file path. Defaults to stdout.",
)
@click.option("--keys", "-k", multiple=True, help="Specific keys to export (repeatable).")
def export_json(vault_name: str, password: str, output: str, keys: tuple):
    """Export secrets as a JSON file."""
    vault = Vault(vault_name)
    if not vault.exists():
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")

    secrets = vault.load(password)
    filter_keys = list(keys) if keys else None

    content = export_secrets(secrets, fmt="json", keys=filter_keys)

    if output:
        Path(output).write_text(content)
        click.echo(f"Exported to {output}")
    else:
        click.echo(content)

    record_event(vault_name, "export", {"format": "json", "output": output or "<stdout>"})


@export_group.command(name="shell")
@click.argument("vault_name")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option(
    "--output", "-o",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Output file path. Defaults to stdout.",
)
@click.option("--keys", "-k", multiple=True, help="Specific keys to export (repeatable).")
def export_shell(vault_name: str, password: str, output: str, keys: tuple):
    """Export secrets as shell export statements."""
    vault = Vault(vault_name)
    if not vault.exists():
        raise click.ClickException(f"Vault '{vault_name}' does not exist.")

    secrets = vault.load(password)
    filter_keys = list(keys) if keys else None

    content = export_secrets(secrets, fmt="shell", keys=filter_keys)

    if output:
        Path(output).write_text(content)
        click.echo(f"Exported to {output}")
    else:
        click.echo(content, nl=False)

    record_event(vault_name, "export", {"format": "shell", "output": output or "<stdout>"})
