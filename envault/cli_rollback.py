"""CLI commands for rolling back secrets."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.rollback import rollback_to_history, rollback_to_checkpoint, list_rollback_points


@click.group("rollback")
def rollback_group() -> None:
    """Rollback secrets to a previous value."""


@rollback_group.command("history")
@click.argument("key")
@click.option("--steps", default=1, show_default=True, help="How many versions back.")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def history_cmd(key: str, steps: int, vault_dir: str, password: str) -> None:
    """Rollback KEY by STEPS history versions."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        result = rollback_to_history(secrets, key, steps)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    if result.restored:
        click.echo(f"Rolled back: {', '.join(result.restored)}")
    for k, reason in result.skipped.items():
        click.echo(f"Skipped {k}: {reason}", err=True)


@rollback_group.command("checkpoint")
@click.argument("name")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def checkpoint_cmd(name: str, vault_dir: str, password: str) -> None:
    """Rollback all keys to values stored in checkpoint NAME."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        result = rollback_to_checkpoint(secrets, name)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    click.echo(f"Restored {len(result.restored)} key(s) from checkpoint '{name}'.")
    for k, reason in result.skipped.items():
        click.echo(f"Skipped {k}: {reason}", err=True)


@rollback_group.command("points")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def points_cmd(key: str, vault_dir: str, password: str) -> None:
    """List available rollback points for KEY."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        points = list_rollback_points(secrets, key)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    if not points:
        click.echo(f"No history found for '{key}'.")
        return
    for idx, entry in enumerate(reversed(points), start=1):
        click.echo(f"  [{idx}] {entry.get('timestamp', 'unknown')}  value={entry.get('value', '')}")
