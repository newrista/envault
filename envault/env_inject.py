"""Inject vault secrets into a subprocess environment."""

from __future__ import annotations

import os
import subprocess
from typing import Dict, List, Optional

from envault.vault import Vault
from envault.alias import resolve_alias
from envault.ttl import is_expired


class ExpiredSecretError(Exception):
    """Raised when a secret with an expired TTL is injected."""


def build_env(
    vault: Vault,
    *,
    prefix: str = "",
    override: bool = True,
    skip_expired: bool = False,
) -> Dict[str, str]:
    """Return an env-var dict built from *vault* secrets.

    Args:
        vault: Loaded :class:`~envault.vault.Vault` instance.
        prefix: Optional prefix prepended to every key name.
        override: When *True* (default) vault values shadow the current
            process environment.  When *False* existing env-vars win.
        skip_expired: When *True* silently drop expired secrets instead of
            raising :class:`ExpiredSecretError`.

    Returns:
        A mapping suitable for passing to :func:`subprocess.run` as *env*.
    """
    base = dict(os.environ)
    secrets = vault.secrets

    for raw_key, value in secrets.items():
        # Skip internal metadata keys
        if raw_key.startswith("__"):
            continue

        # Resolve alias if needed
        resolved = resolve_alias(secrets, raw_key)
        actual_value = secrets.get(resolved, value)

        # TTL check
        if is_expired(secrets, resolved):
            if skip_expired:
                continue
            raise ExpiredSecretError(
                f"Secret '{resolved}' has expired. "
                "Use skip_expired=True to ignore or rotate the secret."
            )

        env_key = f"{prefix}{raw_key}" if prefix else raw_key
        if override or env_key not in base:
            base[env_key] = actual_value

    return base


def run_with_secrets(
    vault: Vault,
    command: List[str],
    *,
    prefix: str = "",
    override: bool = True,
    skip_expired: bool = False,
    **subprocess_kwargs,
) -> subprocess.CompletedProcess:
    """Run *command* with vault secrets injected into its environment.

    Extra keyword arguments are forwarded to :func:`subprocess.run`.
    """
    env = build_env(vault, prefix=prefix, override=override, skip_expired=skip_expired)
    return subprocess.run(command, env=env, **subprocess_kwargs)  # noqa: S603
