"""Namespace support for grouping secrets under a prefix hierarchy."""

from __future__ import annotations

SEPARATOR = "/"
_NS_INDEX_KEY = "__namespaces__"


def _get_ns_index(secrets: dict) -> dict:
    import json
    raw = secrets.get(_NS_INDEX_KEY, "{}")
    return json.loads(raw)


def _set_ns_index(secrets: dict, index: dict) -> None:
    import json
    secrets[_NS_INDEX_KEY] = json.dumps(index)


def make_key(namespace: str, name: str) -> str:
    """Combine a namespace and a bare name into a namespaced key."""
    if not namespace or not name:
        raise ValueError("namespace and name must be non-empty strings")
    return f"{namespace}{SEPARATOR}{name}"


def split_key(key: str) -> tuple[str, str]:
    """Return (namespace, name) for a namespaced key, or ('', key) if flat."""
    if SEPARATOR in key:
        ns, _, name = key.partition(SEPARATOR)
        return ns, name
    return "", key


def register_namespace(secrets: dict, namespace: str, description: str = "") -> None:
    """Register a namespace entry in the index (idempotent)."""
    if not namespace:
        raise ValueError("namespace must be non-empty")
    index = _get_ns_index(secrets)
    if namespace not in index:
        index[namespace] = {"description": description}
    _set_ns_index(secrets, index)


def unregister_namespace(secrets: dict, namespace: str) -> None:
    """Remove a namespace from the index. Raises KeyError if absent."""
    index = _get_ns_index(secrets)
    if namespace not in index:
        raise KeyError(f"Namespace '{namespace}' does not exist")
    del index[namespace]
    _set_ns_index(secrets, index)


def list_namespaces(secrets: dict) -> list[str]:
    """Return sorted list of registered namespaces."""
    return sorted(_get_ns_index(secrets).keys())


def keys_in_namespace(secrets: dict, namespace: str) -> list[str]:
    """Return all secret keys that belong to the given namespace."""
    prefix = namespace + SEPARATOR
    return sorted(
        k for k in secrets
        if k.startswith(prefix) and not k.startswith("__")
    )


def move_to_namespace(secrets: dict, key: str, namespace: str) -> str:
    """Rename a flat key into a namespace, returning the new key."""
    if key not in secrets:
        raise KeyError(f"Key '{key}' not found in vault")
    _, bare = split_key(key)
    new_key = make_key(namespace, bare)
    if new_key in secrets:
        raise ValueError(f"Key '{new_key}' already exists")
    secrets[new_key] = secrets.pop(key)
    return new_key
