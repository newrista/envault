"""CLI commands for cascade vault resolution."""

from __future__ import annotations

import click

from envault.cascade import cascade_resolve, list_overrides
from envault.vault import Vault


@click.group("cascade")
def cascade_group() -> None:
    """Resolve secrets across multiple vaults in priority order."""


@cascade_group.command("resolve")
@click.argument("vault_paths", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True, help="Shared vault password.")
@click.option("--key", "keys", multiple=True, help="Specific keys to resolve (repeatable).")
@click.option("--show-source", is_flag=True, default=False, help="Show which vault provided each value.")
def resolve_cmd(
    vault_paths: tuple,
    password: str,
    keys: tuple,
    show_source: bool,
) -> None:
    """Merge secrets from VAULT_PATHS (lowest to highest priority)."""
    layers = []
    for path in vault_paths:
        v = Vault(path)
        if not v.exists():
            raise click.ClickException(f"Vault not found: {path}")
        try:
            secrets = v.load(password)
        except ValueError:
            raise click.ClickException(f"Wrong password for vault: {path}")
        layers.append((path, secrets))

    result = cascade_resolve(layers, list(keys) if keys else None)

    if not result.resolved:
        click.echo("No secrets resolved.")
        return

    for key, value in sorted(result.resolved.items()):
        if show_source:
            click.echo(f"{key}={value}  # {result.sources[key]}")
        else:
            click.echo(f"{key}={value}")


@cascade_group.command("overrides")
@click.argument("vault_paths", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True, help="Shared vault password.")
def overrides_cmd(vault_paths: tuple, password: str) -> None:
    """Show keys that are overridden across VAULT_PATHS."""
    layers = []
    for path in vault_paths:
        v = Vault(path)
        if not v.exists():
            raise click.ClickException(f"Vault not found: {path}")
        try:
            secrets = v.load(password)
        except ValueError:
            raise click.ClickException(f"Wrong password for vault: {path}")
        layers.append((path, secrets))

    overrides = list_overrides(layers)

    if not overrides:
        click.echo("No overridden keys found.")
        return

    for key, occurrences in sorted(overrides.items()):
        click.echo(f"{key}:")
        for vault_path, value in occurrences:
            click.echo(f"  {vault_path}: {value}")
