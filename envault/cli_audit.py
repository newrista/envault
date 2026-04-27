"""CLI commands for inspecting the envault audit log."""

import click
from typing import Optional

from envault.audit import read_events, filter_events


@click.group("audit")
def audit_group():
    """Inspect the vault audit log."""


@audit_group.command("log")
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
@click.option("--action", default=None, help="Filter by action (set, get, rotate, delete).")
@click.option("--key", default=None, help="Filter by secret key name.")
@click.option("--limit", default=20, show_default=True, help="Maximum number of events to show.")
def show_log(
    vault_dir: str,
    action: Optional[str],
    key: Optional[str],
    limit: int,
) -> None:
    """Display recent audit events for a vault."""
    events = read_events(vault_dir)
    events = filter_events(events, action=action, key=key)
    if not events:
        click.echo("No audit events found.")
        return
    shown = events[-limit:]
    for e in shown:
        actor = e.get("actor", "unknown")
        note = f"  # {e['note']}" if e.get("note") else ""
        click.echo(
            f"[{e['timestamp']}] {actor} {e['action'].upper()} {e['key']}{note}"
        )


@audit_group.command("stats")
@click.option("--vault-dir", default=".", show_default=True, help="Path to vault directory.")
def show_stats(vault_dir: str) -> None:
    """Show summary statistics for vault audit events."""
    events = read_events(vault_dir)
    if not events:
        click.echo("No audit events found.")
        return
    action_counts: dict = {}
    key_counts: dict = {}
    for e in events:
        action_counts[e["action"]] = action_counts.get(e["action"], 0) + 1
        key_counts[e["key"]] = key_counts.get(e["key"], 0) + 1
    click.echo(f"Total events: {len(events)}")
    click.echo("\nBy action:")
    for act, count in sorted(action_counts.items()):
        click.echo(f"  {act}: {count}")
    click.echo("\nMost accessed keys:")
    top_keys = sorted(key_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    for k, count in top_keys:
        click.echo(f"  {k}: {count}")
