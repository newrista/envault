"""CLI commands for merging vaults."""

from __future__ import annotations

import click

from envault.merge import ConflictStrategy, merge_secrets
from envault.vault import Vault


@click.group("merge")
def merge_group() -> None:
    """Merge secrets between vaults."""


@merge_group.command("run")
@click.argument("src_vault_dir")
@click.argument("dst_vault_dir")
@click.option("--src-password", prompt=True, hide_input=True, help="Source vault password.")
@click.option("--dst-password", prompt=True, hide_input=True, help="Destination vault password.")
@click.option(
    "--strategy",
    type=click.Choice([s.value for s in ConflictStrategy], case_sensitive=False),
    default=ConflictStrategy.KEEP.value,
    show_default=True,
    help="Conflict resolution strategy.",
)
@click.option("--keys", default=None, help="Comma-separated list of keys to merge.")
@click.option("--prefix", default=None, help="Only merge keys starting with this prefix.")
@click.option("--dry-run", is_flag=True, default=False, help="Preview changes without writing.")
def run_cmd(
    src_vault_dir: str,
    dst_vault_dir: str,
    src_password: str,
    dst_password: str,
    strategy: str,
    keys: str | None,
    prefix: str | None,
    dry_run: bool,
) -> None:
    """Merge secrets from SRC_VAULT_DIR into DST_VAULT_DIR."""
    src_vault = Vault(src_vault_dir)
    if not src_vault.exists():
        raise click.ClickException(f"Source vault not found: {src_vault_dir}")

    dst_vault = Vault(dst_vault_dir)
    if not dst_vault.exists():
        raise click.ClickException(f"Destination vault not found: {dst_vault_dir}")

    src_secrets = src_vault.load(src_password)
    dst_secrets = dst_vault.load(dst_password)

    key_list = [k.strip() for k in keys.split(",")] if keys else None
    strat = ConflictStrategy(strategy.lower())

    # Work on a copy for dry-run so we don't mutate the real dict
    target = dict(dst_secrets) if dry_run else dst_secrets

    result = merge_secrets(src_secrets, target, strategy=strat, keys=key_list, prefix=prefix)

    if result.added:
        click.echo(f"Added ({len(result.added)}): {', '.join(result.added)}")
    if result.overwritten:
        click.echo(f"Overwritten ({len(result.overwritten)}): {', '.join(result.overwritten)}")
    if result.skipped:
        click.echo(f"Skipped ({len(result.skipped)}): {', '.join(result.skipped)}")
    if result.errors:
        for err in result.errors:
            click.echo(f"Error: {err}", err=True)

    if dry_run:
        click.echo("Dry run — no changes written.")
        return

    if not result.added and not result.overwritten:
        click.echo("Nothing to merge.")
        return

    dst_vault.save(dst_secrets, dst_password)
    click.echo("Merge complete.")
