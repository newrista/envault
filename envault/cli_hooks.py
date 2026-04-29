"""CLI commands for managing envault lifecycle hooks."""

import click
from pathlib import Path
from envault.hooks import register_hook, unregister_hook, list_hooks, HOOK_EVENTS


@click.group("hooks")
def hooks_group():
    """Manage pre/post lifecycle hooks for vault events."""


@hooks_group.command("add")
@click.argument("event", type=click.Choice(HOOK_EVENTS))
@click.argument("command")
@click.option("--vault-dir", default=".", help="Path to vault directory.")
def add_cmd(event, command, vault_dir):
    """Register a shell COMMAND to run on EVENT."""
    try:
        register_hook(Path(vault_dir), event, command)
        click.echo(f"Hook registered: [{event}] -> {command}")
    except ValueError as e:
        raise click.ClickException(str(e))


@hooks_group.command("remove")
@click.argument("event", type=click.Choice(HOOK_EVENTS))
@click.argument("command")
@click.option("--vault-dir", default=".", help="Path to vault directory.")
def remove_cmd(event, command, vault_dir):
    """Unregister a hook COMMAND from EVENT."""
    try:
        unregister_hook(Path(vault_dir), event, command)
        click.echo(f"Hook removed: [{event}] -> {command}")
    except (ValueError, KeyError) as e:
        raise click.ClickException(str(e))


@hooks_group.command("list")
@click.option("--event", type=click.Choice(HOOK_EVENTS), default=None, help="Filter by event.")
@click.option("--vault-dir", default=".", help="Path to vault directory.")
def list_cmd(event, vault_dir):
    """List all registered hooks."""
    try:
        hooks = list_hooks(Path(vault_dir), event=event)
    except ValueError as e:
        raise click.ClickException(str(e))

    any_found = False
    for ev, commands in hooks.items():
        for cmd in commands:
            click.echo(f"{ev:<15} {cmd}")
            any_found = True
    if not any_found:
        click.echo("No hooks registered.")
