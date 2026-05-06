"""CLI commands for managing secret namespaces."""

import click
from envault.vault import Vault
from envault.namespace import (
    register_namespace,
    unregister_namespace,
    list_namespaces,
    keys_in_namespace,
    move_to_namespace,
)


@click.group("namespace", help="Manage secret namespaces.")
def namespace_group() -> None:
    pass


@namespace_group.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Optional description.")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def create_cmd(name: str, description: str, vault_dir: str, password: str) -> None:
    """Register a new namespace."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        register_namespace(secrets, name, description)
    except ValueError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Namespace '{name}' created.")


@namespace_group.command("delete")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def delete_cmd(name: str, vault_dir: str, password: str) -> None:
    """Unregister a namespace (does not delete its keys)."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        unregister_namespace(secrets, name)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Namespace '{name}' deleted.")


@namespace_group.command("list")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def list_cmd(vault_dir: str, password: str) -> None:
    """List all registered namespaces."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    namespaces = list_namespaces(secrets)
    if not namespaces:
        click.echo("No namespaces registered.")
    else:
        for ns in namespaces:
            click.echo(ns)


@namespace_group.command("show")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def show_cmd(name: str, vault_dir: str, password: str) -> None:
    """Show all keys belonging to a namespace."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    keys = keys_in_namespace(secrets, name)
    if not keys:
        click.echo(f"No keys found in namespace '{name}'.")
    else:
        for k in keys:
            click.echo(k)


@namespace_group.command("move")
@click.argument("key")
@click.argument("namespace")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def move_cmd(key: str, namespace: str, vault_dir: str, password: str) -> None:
    """Move an existing key into a namespace."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    try:
        new_key = move_to_namespace(secrets, key, namespace)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
    vault.save(secrets, password)
    click.echo(f"Moved '{key}' -> '{new_key}'.")
