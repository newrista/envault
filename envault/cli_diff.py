"""CLI commands for diffing vault secrets."""

from __future__ import annotations

import json

import click

from envault.diff import diff_secrets, format_diff
from envault.vault import Vault


@click.group("diff")
def diff_group() -> None:
    """Compare secrets between two vaults or a vault and a .env file."""


@diff_group.command("vaults")
@click.argument("vault_a")
@click.argument("vault_b")
@click.option("--password-a", prompt="Password for vault A", hide_input=True)
@click.option("--password-b", prompt="Password for vault B", hide_input=True)
@click.option("--show-values", is_flag=True, default=False, help="Reveal secret values.")
def diff_vaults(
    vault_a: str,
    vault_b: str,
    password_a: str,
    password_b: str,
    show_values: bool,
) -> None:
    """Diff secrets between two named vaults."""
    try:
        old_secrets = Vault(vault_a).load(password_a)
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault '{vault_a}': {exc}") from exc

    try:
        new_secrets = Vault(vault_b).load(password_b)
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault '{vault_b}': {exc}") from exc

    result = diff_secrets(old_secrets, new_secrets, show_values=show_values)
    click.echo(f"Comparing '{vault_a}' -> '{vault_b}': {result.summary()}")
    for line in format_diff(result, show_values=show_values):
        click.echo(line)


@diff_group.command("dotenv")
@click.argument("vault_name")
@click.argument("dotenv_file", type=click.Path(exists=True))
@click.option("--password", prompt=True, hide_input=True)
@click.option("--show-values", is_flag=True, default=False, help="Reveal secret values.")
def diff_dotenv(
    vault_name: str,
    dotenv_file: str,
    password: str,
    show_values: bool,
) -> None:
    """Diff a vault against a .env file."""
    try:
        vault_secrets = Vault(vault_name).load(password)
    except Exception as exc:
        raise click.ClickException(f"Failed to load vault '{vault_name}': {exc}") from exc

    from envault.import_secrets import from_dotenv

    with open(dotenv_file) as fh:
        dotenv_secrets = from_dotenv(fh.read())

    result = diff_secrets(vault_secrets, dotenv_secrets, show_values=show_values)
    click.echo(f"Comparing vault '{vault_name}' -> '{dotenv_file}': {result.summary()}")
    for line in format_diff(result, show_values=show_values):
        click.echo(line)
