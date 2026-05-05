"""CLI commands for vault compression (backup / restore)."""

from __future__ import annotations

from pathlib import Path

import click

from envault.compress import backup_vault, restore_vault
from envault.vault import Vault


@click.group("compress", help="Compress and decompress vault backups.")
def compress_group() -> None:  # pragma: no cover
    pass


@compress_group.command("backup")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.argument("dest")
def backup_cmd(vault_dir: str, password: str, dest: str) -> None:
    """Compress the vault and write a backup archive to DEST."""
    vault = Vault(Path(vault_dir))
    if not vault.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    dest_path = Path(dest)
    try:
        n = backup_vault(vault, password, dest_path)
        click.echo(f"Backed up {n} secret(s) to {dest_path}.")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc


@compress_group.command("restore")
@click.option("--vault-dir", default=".", show_default=True, help="Vault directory.")
@click.option("--password", prompt=True, hide_input=True, help="Vault password.")
@click.argument("src")
def restore_cmd(vault_dir: str, password: str, src: str) -> None:
    """Restore secrets from a compressed backup archive SRC into the vault."""
    vault = Vault(Path(vault_dir))
    if not vault.exists():
        raise click.ClickException("No vault found. Run 'envault init' first.")
    src_path = Path(src)
    try:
        n = restore_vault(vault, password, src_path)
        click.echo(f"Restored {n} secret(s) from {src_path}.")
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
