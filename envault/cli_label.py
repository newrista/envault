"""CLI commands for managing key labels."""

from __future__ import annotations

import click

from envault.label import get_label, list_labels, remove_label, set_label
from envault.vault import Vault


@click.group("label")
def label_group() -> None:
    """Manage human-friendly labels for secret keys."""


@label_group.command("set")
@click.argument("key")
@click.argument("label")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", envvar="ENVAULT_PASSWORD", prompt=True)
def set_cmd(key: str, label: str, vault_dir: str, password: str) -> None:
    """Attach LABEL to KEY."""
    vault = Vault(vault_dir)
    if not vault.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    secrets = vault.load(password)
    try:
        set_label(secrets, key, label)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Label set for '{key}': {label}")


@label_group.command("get")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", envvar="ENVAULT_PASSWORD", prompt=True)
def get_cmd(key: str, vault_dir: str, password: str) -> None:
    """Show the label for KEY."""
    vault = Vault(vault_dir)
    if not vault.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    secrets = vault.load(password)
    label = get_label(secrets, key)
    if label is None:
        click.echo(f"No label set for '{key}'.")
    else:
        click.echo(label)


@label_group.command("remove")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", envvar="ENVAULT_PASSWORD", prompt=True)
def remove_cmd(key: str, vault_dir: str, password: str) -> None:
    """Remove the label from KEY."""
    vault = Vault(vault_dir)
    if not vault.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    secrets = vault.load(password)
    try:
        remove_label(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets, password)
    click.echo(f"Label removed from '{key}'.")


@label_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", envvar="ENVAULT_PASSWORD", prompt=True)
def list_cmd(vault_dir: str, password: str) -> None:
    """List all labelled keys."""
    vault = Vault(vault_dir)
    if not vault.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    secrets = vault.load(password)
    labels = list_labels(secrets)
    if not labels:
        click.echo("No labels defined.")
        return
    for key, label in sorted(labels.items()):
        click.echo(f"{key}: {label}")
