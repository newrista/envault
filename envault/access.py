"""Access control for vault secrets — define read/write permissions per key or pattern."""

from __future__ import annotations

import fnmatch
from typing import Dict, List, Optional

ACCESS_META_KEY = "__access_policy__"

PERM_READ = "read"
PERM_WRITE = "write"
PERM_DENY = "deny"


def _get_policy(secrets: Dict[str, str]) -> Dict[str, List[str]]:
    """Return the access policy dict stored inside the secrets map."""
    import json
    raw = secrets.get(ACCESS_META_KEY, "{}")
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _set_policy(secrets: Dict[str, str], policy: Dict[str, List[str]]) -> None:
    """Persist the access policy dict back into the secrets map."""
    import json
    secrets[ACCESS_META_KEY] = json.dumps(policy)


def set_permission(secrets: Dict[str, str], key: str, perms: List[str]) -> None:
    """Assign a list of permissions to a key or glob pattern."""
    valid = {PERM_READ, PERM_WRITE, PERM_DENY}
    for p in perms:
        if p not in valid:
            raise ValueError(f"Unknown permission '{p}'. Valid: {valid}")
    policy = _get_policy(secrets)
    policy[key] = list(set(perms))
    _set_policy(secrets, policy)


def get_permission(secrets: Dict[str, str], key: str) -> List[str]:
    """Return effective permissions for *key* by checking exact match then globs."""
    policy = _get_policy(secrets)
    if key in policy:
        return policy[key]
    for pattern, perms in policy.items():
        if fnmatch.fnmatch(key, pattern):
            return perms
    return [PERM_READ, PERM_WRITE]  # default: full access


def remove_permission(secrets: Dict[str, str], key: str) -> bool:
    """Remove any explicit permission rule for *key*. Returns True if removed."""
    policy = _get_policy(secrets)
    if key in policy:
        del policy[key]
        _set_policy(secrets, policy)
        return True
    return False


def list_permissions(secrets: Dict[str, str]) -> Dict[str, List[str]]:
    """Return all explicitly defined permission rules."""
    return dict(_get_policy(secrets))


def check_access(secrets: Dict[str, str], key: str, required: str) -> bool:
    """Return True if *required* permission is granted for *key*."""
    perms = get_permission(secrets, key)
    if PERM_DENY in perms:
        return False
    return required in perms
