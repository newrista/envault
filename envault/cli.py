"""CLI entry point for envault."""

import click
from envault.vault import Vault
from envault.rotation import rotate_secret, list_stale_secrets


@click.group()
def cli():
    """envault — secure environment variable manager."""
    pass


@cli.command()
@click.argument("vault_path")
@click.password_option(prompt="Master password")
def init_vault(vault_path, password):
    """Initialise a new vault at VAULT_PATH."""
    vault = Vault(vault_path, password)
    if vault.exists():
        click.echo(f"Vault already exists at {vault_path}")
        return
    vault.save({})
    click.echo(f"Vault initialised at {vault_path}")


@cli.command()
@click.argument("vault_path")
@click.argument("key")
@click.argument("value")
@click.password_option(prompt="Master password")
def set_secret(vault_path, key, value, password):
    """Store or update a secret KEY=VALUE in the vault."""
    vault = Vault(vault_path, password)
    secrets = vault.load()
    secrets[key] = value
    vault.save(secrets)
    click.echo(f"Secret '{key}' saved.")


@cli.command()
@click.argument("vault_path")
@click.argument("key")
@click.password_option(prompt="Master password")
def get_secret(vault_path, key, password):
    """Retrieve a secret by KEY from the vault."""
    vault = Vault(vault_path, password)
    secrets = vault.load()
    if key not in secrets:
        click.echo(f"Key '{key}' not found.", err=True)
        raise SystemExit(1)
    click.echo(secrets[key])


@cli.command()
@click.argument("vault_path")
@click.password_option(prompt="Master password")
def list_vaults(vault_path, password):
    """List all secret keys stored in the vault."""
    vault = Vault(vault_path, password)
    secrets = vault.load()
    keys = [k for k in secrets if not k.startswith("__")]
    for key in keys:
        click.echo(key)


@cli.command()
@click.argument("vault_path")
@click.argument("key")
@click.argument("new_value")
@click.password_option(prompt="Master password")
def rotate(vault_path, key, new_value, password):
    """Rotate a secret KEY to NEW_VALUE and record rotation timestamp."""
    vault = Vault(vault_path, password)
    secrets = vault.load()
    if key not in secrets:
        click.echo(f"Key '{key}' not found.", err=True)
        raise SystemExit(1)
    secrets = rotate_secret(secrets, key, new_value)
    vault.save(secrets)
    click.echo(f"Secret '{key}' rotated successfully.")


@cli.command()
@click.argument("vault_path")
@click.option("--max-age", default=90, show_default=True, help="Max age in days before rotation is due.")
@click.password_option(prompt="Master password")
def check_rotation(vault_path, max_age, password):
    """List secrets that are due for rotation."""
    vault = Vault(vault_path, password)
    secrets = vault.load()
    stale = list_stale_secrets(secrets, max_age_days=max_age)
    if not stale:
        click.echo("All secrets are up to date.")
    else:
        click.echo("Secrets due for rotation:")
        for key in stale:
            click.echo(f"  - {key}")


if __name__ == "__main__":
    cli()
