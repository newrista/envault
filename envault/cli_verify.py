"""CLI commands for vault verification."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.verify import verify_secrets


@click.group("verify")
def verify_group() -> None:
    """Verify vault secrets against schemas, TTL, and pin rules."""


@verify_group.command("run")
@click.option("--vault-dir", default=".", show_default=True, help="Path to the vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--strict", is_flag=True, default=False, help="Exit with non-zero code if warnings exist.")
@click.option("--only-errors", is_flag=True, default=False, help="Show only errors.")
def run_cmd(vault_dir: str, password: str, strict: bool, only_errors: bool) -> None:
    """Run verification checks on all secrets in the vault."""
    vault = Vault(vault_dir)
    if not vault.exists():
        click.echo("No vault found. Run `envault init` first.", err=True)
        raise SystemExit(1)

    secrets = vault.load(password)
    report = verify_secrets(secrets)

    issues = report.errors() if only_errors else report.issues

    if not issues:
        click.echo(click.style("✔ All checks passed.", fg="green"))
        return

    level_colors = {"error": "red", "warning": "yellow", "info": "cyan"}
    for issue in issues:
        color = level_colors.get(issue.level, "white")
        prefix = issue.level.upper().ljust(7)
        click.echo(f"{click.style(prefix, fg=color)}  {issue.key}: {issue.message}")

    click.echo(f"\nSummary: {report.summary()}")

    if report.has_errors() or (strict and report.warnings()):
        raise SystemExit(1)
