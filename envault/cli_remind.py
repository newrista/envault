"""CLI commands for the reminder / notification feature."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.remind import expiring_soon, rotation_overdue, reminder_report


@click.group("remind")
def remind_group() -> None:
    """Reminders for expiring or stale secrets."""


@remind_group.command("expiring")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--within", default=86400, show_default=True, help="Look-ahead window in seconds.")
def expiring_cmd(vault_dir: str, password: str, within: int) -> None:
    """List secrets expiring within a time window."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    items = expiring_soon(secrets, within_seconds=within)
    if not items:
        click.echo("No secrets expiring within the specified window.")
        return
    for item in items:
        click.echo(f"  {item['key']:30s}  expires at {item['expires_at']}  ({item['seconds_remaining']}s remaining)")


@remind_group.command("stale")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
def stale_cmd(vault_dir: str, password: str) -> None:
    """List secrets whose rotation is overdue."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    items = rotation_overdue(secrets)
    if not items:
        click.echo("No secrets are overdue for rotation.")
        return
    for item in items:
        click.echo(f"  {item['key']:30s}  last rotated: {item['last_rotated']}")


@remind_group.command("report")
@click.option("--vault-dir", default=".", show_default=True)
@click.option("--password", prompt=True, hide_input=True)
@click.option("--within", default=86400, show_default=True)
def report_cmd(vault_dir: str, password: str, within: int) -> None:
    """Full reminder report: expiring secrets and overdue rotations."""
    vault = Vault(vault_dir)
    secrets = vault.load(password)
    report = reminder_report(secrets, within_seconds=within)

    click.echo("=== Expiring Soon ===")
    if report["expiring_soon"]:
        for item in report["expiring_soon"]:
            click.echo(f"  {item['key']:30s}  {item['expires_at']}  ({item['seconds_remaining']}s)")
    else:
        click.echo("  None")

    click.echo("=== Rotation Overdue ===")
    if report["rotation_overdue"]:
        for item in report["rotation_overdue"]:
            click.echo(f"  {item['key']:30s}  last rotated: {item['last_rotated']}")
    else:
        click.echo("  None")
