"""Pre/post hooks for secret lifecycle events in envault vaults."""

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

HOOK_EVENTS = ("pre_set", "post_set", "pre_delete", "post_delete", "pre_rotate", "post_rotate")

_registry: Dict[str, List[Callable]] = {event: [] for event in HOOK_EVENTS}


def _hooks_path(vault_dir: Path) -> Path:
    return vault_dir / ".hooks.json"


def _load_hooks(vault_dir: Path) -> Dict[str, List[str]]:
    path = _hooks_path(vault_dir)
    if not path.exists():
        return {event: [] for event in HOOK_EVENTS}
    with open(path) as f:
        return json.load(f)


def _save_hooks(vault_dir: Path, hooks: Dict[str, List[str]]) -> None:
    with open(_hooks_path(vault_dir), "w") as f:
        json.dump(hooks, f, indent=2)


def register_hook(vault_dir: Path, event: str, command: str) -> None:
    """Register a shell command to run on the given lifecycle event."""
    if event not in HOOK_EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
    hooks = _load_hooks(vault_dir)
    if command not in hooks.get(event, []):
        hooks.setdefault(event, []).append(command)
        _save_hooks(vault_dir, hooks)


def unregister_hook(vault_dir: Path, event: str, command: str) -> None:
    """Remove a previously registered hook command."""
    if event not in HOOK_EVENTS:
        raise ValueError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
    hooks = _load_hooks(vault_dir)
    try:
        hooks[event].remove(command)
    except (KeyError, ValueError):
        raise KeyError(f"Hook '{command}' not found for event '{event}'")
    _save_hooks(vault_dir, hooks)


def list_hooks(vault_dir: Path, event: Optional[str] = None) -> Dict[str, List[str]]:
    """List all registered hooks, optionally filtered by event."""
    hooks = _load_hooks(vault_dir)
    if event is not None:
        if event not in HOOK_EVENTS:
            raise ValueError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
        return {event: hooks.get(event, [])}
    return hooks


def fire_hook(vault_dir: Path, event: str, context: Optional[Dict] = None) -> List[str]:
    """Execute all shell commands registered for the given event.
    Returns list of commands that were fired."""
    import subprocess
    if event not in HOOK_EVENTS:
        raise ValueError(f"Unknown event '{event}'.")
    hooks = _load_hooks(vault_dir)
    commands = hooks.get(event, [])
    env_context = {k: str(v) for k, v in (context or {}).items()}
    fired = []
    for cmd in commands:
        subprocess.run(cmd, shell=True, env={**__import__('os').environ, **env_context})
        fired.append(cmd)
    return fired
