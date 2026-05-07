"""CLI commands for vault watermarking."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.watermark import stamp, verify, remove


@click.group("watermark", help="Embed and verify tamper-evident watermarks in a vault.")
def watermark_group() -> None:
    pass


@watermark_group.command("stamp")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.option("--label", default="", show_default=True, help="Human-readable label for this watermark.")
def stamp_cmd(vault_dir: str, password: str, label: str) -> None:
    """Embed a watermark fingerprint into the vault."""
    v = Vault(vault_dir)
    if not v.exists():
        raise click.ClickException("Vault not found. Run 'envault init' first.")
    secrets = v.load(password)
    stamp(secrets, label=label)
    v.save(secrets, password)
    click.echo(f"Watermark stamped. label={label!r}")


@watermark_group.command("verify")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def verify_cmd(vault_dir: str, password: str) -> None:
    """Verify the watermark embedded in the vault."""
    v = Vault(vault_dir)
    if not v.exists():
        raise click.ClickException("Vault not found.")
    secrets = v.load(password)
    result = verify(secrets)
    if not result.present:
        click.echo("No watermark found in vault.")
        raise SystemExit(1)
    if result.valid:
        click.echo(f"Watermark OK  label={result.label!r}  fingerprint={result.fingerprint}")
    else:
        click.echo("Watermark INVALID — vault contents may have been tampered with.", err=True)
        raise SystemExit(2)


@watermark_group.command("remove")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
def remove_cmd(vault_dir: str, password: str) -> None:
    """Remove the watermark from the vault."""
    v = Vault(vault_dir)
    if not v.exists():
        raise click.ClickException("Vault not found.")
    secrets = v.load(password)
    remove(secrets)
    v.save(secrets, password)
    click.echo("Watermark removed.")
