"""CLI commands for vault health scoring."""
from __future__ import annotations

import click

from envault.vault import Vault
from envault.scoring import score_vault


@click.group("score")
def scoring_group() -> None:
    """Vault health scoring commands."""


@scoring_group.command("show")
@click.option("--vault-dir", default=".", show_default=True,
              help="Directory containing the vault.")
@click.option("--password", prompt=True, hide_input=True,
              help="Vault password.")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Output raw JSON breakdown.")
def show_cmd(vault_dir: str, password: str, as_json: bool) -> None:
    """Display the health score for a vault."""
    v = Vault(vault_dir)
    if not v.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    secrets = v.load(password)
    report = score_vault(secrets)

    if as_json:
        import json
        click.echo(json.dumps({
            "score": report.score,
            "grade": _grade(report.score),
            "total_keys": report.total_keys,
            "expired_count": report.expired_count,
            "stale_count": report.stale_count,
            "no_schema_count": report.no_schema_count,
            "breakdown": report.breakdown,
        }, indent=2))
    else:
        click.echo(report.summary())
        if report.expired_count:
            click.echo(click.style(
                f"  ✗ {report.expired_count} expired secret(s) (-{report.breakdown['expired_penalty']} pts)",
                fg="red"))
        if report.stale_count:
            click.echo(click.style(
                f"  ⚠ {report.stale_count} stale rotation(s) (-{report.breakdown['stale_penalty']} pts)",
                fg="yellow"))
        if report.no_schema_count:
            click.echo(
                f"  ℹ {report.no_schema_count} key(s) without schema "
                f"(-{report.breakdown['no_schema_penalty']} pts)")


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"
