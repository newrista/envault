"""CLI commands for vault secret inheritance."""
from __future__ import annotations

import click

from .vault import Vault
from .inherit import (
    get_inherit_chain,
    set_inherit_chain,
    resolve_inherited,
    list_inherited_keys,
)


@click.group("inherit", help="Manage secret inheritance chains between vaults.")
def inherit_group() -> None:  # pragma: no cover
    pass


@inherit_group.command("set-chain")
@click.argument("vault_dir")
@click.argument("password")
@click.argument("parents", nargs=-1, required=True)
def set_chain_cmd(vault_dir: str, password: str, parents: tuple[str, ...]) -> None:
    """Set the ordered list of PARENTS (vault paths) for VAULT_DIR."""
    v = Vault(vault_dir)
    if not v.exists():
        click.echo("Error: vault not initialised.", err=True)
        raise SystemExit(1)
    secrets = v.load(password)
    set_inherit_chain(secrets, list(parents))
    v.save(secrets, password)
    click.echo(f"Inheritance chain set: {' -> '.join(parents)}")


@inherit_group.command("show-chain")
@click.argument("vault_dir")
@click.argument("password")
def show_chain_cmd(vault_dir: str, password: str) -> None:
    """Display the current inheritance chain for VAULT_DIR."""
    v = Vault(vault_dir)
    if not v.exists():
        click.echo("Error: vault not initialised.", err=True)
        raise SystemExit(1)
    secrets = v.load(password)
    chain = get_inherit_chain(secrets)
    if not chain:
        click.echo("No inheritance chain configured.")
    else:
        for i, parent in enumerate(chain):
            click.echo(f"  [{i}] {parent}")


@inherit_group.command("resolve")
@click.argument("key")
@click.argument("vault_dirs", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True)
def resolve_cmd(key: str, vault_dirs: tuple[str, ...], password: str) -> None:
    """Resolve KEY by walking VAULT_DIRS in priority order."""
    vault_secrets_list = []
    for vd in vault_dirs:
        v = Vault(vd)
        if not v.exists():
            click.echo(f"Warning: vault {vd!r} does not exist, skipping.", err=True)
            continue
        vault_secrets_list.append(v.load(password))
    try:
        result = resolve_inherited(key, vault_secrets_list)
        click.echo(f"{result.value}  (from vault index {result.source_index})")
    except KeyError as exc:
        click.echo(str(exc), err=True)
        raise SystemExit(1)


@inherit_group.command("list")
@click.argument("vault_dirs", nargs=-1, required=True)
@click.option("--password", prompt=True, hide_input=True)
def list_cmd(vault_dirs: tuple[str, ...], password: str) -> None:
    """List all resolvable keys across VAULT_DIRS with their source index."""
    vault_secrets_list = []
    for vd in vault_dirs:
        v = Vault(vd)
        if v.exists():
            vault_secrets_list.append(v.load(password))
    mapping = list_inherited_keys(vault_secrets_list)
    if not mapping:
        click.echo("No keys found.")
        return
    for key, idx in sorted(mapping.items()):
        click.echo(f"  {key:<30} (vault index {idx})")
