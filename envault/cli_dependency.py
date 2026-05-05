"""CLI commands for secret dependency management."""
import click
from envault.vault import Vault
from envault.dependency import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    dependency_graph,
)


@click.group("deps")
def deps_group() -> None:
    """Manage secret dependencies."""


@deps_group.command("add")
@click.argument("key")
@click.argument("depends_on")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def add_cmd(key: str, depends_on: str, vault_dir: str, password: str) -> None:
    """Declare that KEY depends on DEPENDS_ON."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        add_dependency(secrets, key, depends_on)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    click.echo(f"Added dependency: {key} -> {depends_on}")


@deps_group.command("remove")
@click.argument("key")
@click.argument("depends_on")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def remove_cmd(key: str, depends_on: str, vault_dir: str, password: str) -> None:
    """Remove the dependency of KEY on DEPENDS_ON."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    try:
        remove_dependency(secrets, key, depends_on)
    except KeyError as exc:
        raise click.ClickException(str(exc))
    v.save(secrets, password)
    click.echo(f"Removed dependency: {key} -> {depends_on}")


@deps_group.command("show")
@click.argument("key")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def show_cmd(key: str, vault_dir: str, password: str) -> None:
    """Show dependencies of KEY and which secrets depend on it."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    deps = get_dependencies(secrets, key)
    rdeps = get_dependents(secrets, key)
    click.echo(f"Dependencies of '{key}': {', '.join(deps) if deps else '(none)'}")
    click.echo(f"Dependents on '{key}': {', '.join(rdeps) if rdeps else '(none)'}")


@deps_group.command("graph")
@click.option("--vault-dir", default=".", show_default=True)
@click.password_option("--password", prompt="Vault password")
def graph_cmd(vault_dir: str, password: str) -> None:
    """Print the full dependency graph."""
    v = Vault(vault_dir)
    secrets = v.load(password)
    graph = dependency_graph(secrets)
    if not graph:
        click.echo("No dependencies defined.")
        return
    for key, deps in sorted(graph.items()):
        click.echo(f"  {key} -> {', '.join(deps)}")
