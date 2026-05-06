"""CLI commands for quota management."""

from __future__ import annotations

import click
from envault.vault import Vault
from envault.quota import set_quota, get_quota, quota_status


@click.group("quota")
def quota_group() -> None:
    """Manage vault quotas (secret count and value size limits)."""


@quota_group.command("set")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--max-secrets", type=int, default=None, help="Maximum number of secrets.")
@click.option("--max-value-bytes", type=int, default=None, help="Maximum value size in bytes.")
def set_cmd(vault_dir: str, password: str, max_secrets: int | None, max_value_bytes: int | None) -> None:
    """Set quota limits for the vault."""
    if max_secrets is None and max_value_bytes is None:
        raise click.UsageError("Provide at least one of --max-secrets or --max-value-bytes.")
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    try:
        set_quota(secrets, max_secrets=max_secrets, max_value_bytes=max_value_bytes)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    vault.save(secrets)
    click.echo("Quota updated.")


@quota_group.command("show")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def show_cmd(vault_dir: str, password: str) -> None:
    """Show current quota settings."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    q = get_quota(secrets)
    click.echo(f"max_secrets    : {q['max_secrets']}")
    click.echo(f"max_value_bytes: {q['max_value_bytes']}")


@quota_group.command("status")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def status_cmd(vault_dir: str, password: str) -> None:
    """Show quota usage status."""
    vault = Vault(vault_dir, password)
    secrets = vault.load()
    s = quota_status(secrets)
    click.echo(f"Secrets used    : {s['used_secrets']} / {s['max_secrets']}")
    click.echo(f"Remaining slots : {s['remaining_secrets']}")
    click.echo(f"Max value size  : {s['max_value_bytes']} bytes")
    pct = s["used_secrets"] / s["max_secrets"] * 100 if s["max_secrets"] else 0
    click.echo(f"Usage           : {pct:.1f}%")
