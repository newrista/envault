"""Tag management for envault secrets."""

from __future__ import annotations

from typing import Dict, List, Optional

_TAGS_KEY = "__tags__"


def _get_tags_index(secrets: Dict[str, str]) -> Dict[str, List[str]]:
    """Return the tags index stored inside the secrets dict."""
    import json

    raw = secrets.get(_TAGS_KEY, "{}")
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


def _set_tags_index(secrets: Dict[str, str], index: Dict[str, List[str]]) -> None:
    """Persist the tags index back into the secrets dict."""
    import json

    secrets[_TAGS_KEY] = json.dumps(index)


def add_tag(secrets: Dict[str, str], key: str, tag: str) -> None:
    """Add *tag* to *key*.  Raises KeyError if *key* does not exist."""
    if key not in secrets or key == _TAGS_KEY:
        raise KeyError(f"Secret '{key}' not found.")
    index = _get_tags_index(secrets)
    tags = index.get(key, [])
    if tag not in tags:
        tags.append(tag)
    index[key] = tags
    _set_tags_index(secrets, index)


def remove_tag(secrets: Dict[str, str], key: str, tag: str) -> None:
    """Remove *tag* from *key*.  Silently ignores missing tags."""
    index = _get_tags_index(secrets)
    tags = index.get(key, [])
    index[key] = [t for t in tags if t != tag]
    _set_tags_index(secrets, index)


def get_tags(secrets: Dict[str, str], key: str) -> List[str]:
    """Return the list of tags for *key*."""
    return _get_tags_index(secrets).get(key, [])


def list_by_tag(secrets: Dict[str, str], tag: str) -> List[str]:
    """Return all secret keys that carry *tag*."""
    index = _get_tags_index(secrets)
    return [k for k, tags in index.items() if tag in tags]


def all_tags(secrets: Dict[str, str]) -> Dict[str, List[str]]:
    """Return the full tags index (key -> list[tag])."""
    return dict(_get_tags_index(secrets))
