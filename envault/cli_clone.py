"""CLI commands for cloning secrets between vaults."""

from __future__ import annotations

import click

from envault.vault import Vault
from envault.clone import clone_secrets


@click.group("clone")
def clone_group() -> None:
    """Clone secrets from one vault into another."""


@clone_group.command("run")
@click.argument("src_dir", type=click.Path(exists=True, file_okay=False))
@click.argument("dst_dir", type=click.Path(file_okay=False))
@click.password_option("--src-password", prompt="Source vault password", confirmation_prompt=False)
@click.password_option("--dst-password", prompt="Destination vault password", confirmation_prompt=False)
@click.option("--pattern", default=None, help="Glob pattern to filter keys (e.g. 'DB_*').")
@click.option("--key", "keys", multiple=True, help="Explicit key(s) to clone.")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing keys in destination.")
def run_cmd(
    src_dir: str,
    dst_dir: str,
    src_password: str,
    dst_password: str,
    pattern: str | None,
    keys: tuple[str, ...],
    overwrite: bool,
) -> None:
    """Clone secrets from SRC_DIR vault into DST_DIR vault."""
    src_vault = Vault(src_dir, src_password)
    if not src_vault.exists():
        raise click.ClickException(f"Source vault not found: {src_dir}")
    src_vault.load()

    dst_vault = Vault(dst_dir, dst_password)
    if not dst_vault.exists():
        dst_vault.secrets = {}
        dst_vault.save()
    else:
        dst_vault.load()

    try:
        result = clone_secrets(
            src_vault,
            dst_vault,
            pattern=pattern or None,
            keys=list(keys) if keys else None,
            overwrite=overwrite,
        )
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc

    copied = [k for k, v in result.items() if v == "copied"]
    skipped = [k for k, v in result.items() if v == "skipped"]

    if copied:
        click.echo(f"Copied {len(copied)} key(s): {', '.join(sorted(copied))}")
    if skipped:
        click.echo(f"Skipped {len(skipped)} existing key(s): {', '.join(sorted(skipped))}")
    if not copied and not skipped:
        click.echo("No matching keys found in source vault.")
