"""Search and filter secrets within a vault."""

from __future__ import annotations

import fnmatch
import re
from typing import Dict, List, Optional, Tuple


def search_keys(
    secrets: Dict[str, str],
    pattern: str,
    use_regex: bool = False,
) -> List[str]:
    """Return secret keys matching *pattern*.

    Args:
        secrets: Mapping of key -> value loaded from a vault.
        pattern: Glob-style pattern (default) or regex when *use_regex* is True.
        use_regex: Treat *pattern* as a regular expression.

    Returns:
        Sorted list of matching keys.
    """
    matches: List[str] = []
    if use_regex:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc
        matches = [k for k in secrets if compiled.search(k)]
    else:
        matches = fnmatch.filter(list(secrets.keys()), pattern)
    return sorted(matches)


def search_values(
    secrets: Dict[str, str],
    pattern: str,
    use_regex: bool = False,
) -> List[Tuple[str, str]]:
    """Return (key, value) pairs whose *value* matches *pattern*.

    Args:
        secrets: Mapping of key -> value loaded from a vault.
        pattern: Glob-style pattern (default) or regex when *use_regex* is True.
        use_regex: Treat *pattern* as a regular expression.

    Returns:
        Sorted list of (key, value) tuples.
    """
    results: List[Tuple[str, str]] = []
    if use_regex:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc
        results = [(k, v) for k, v in secrets.items() if compiled.search(v)]
    else:
        results = [
            (k, v) for k, v in secrets.items() if fnmatch.fnmatch(v, pattern)
        ]
    return sorted(results, key=lambda t: t[0])


def search_secrets(
    secrets: Dict[str, str],
    pattern: str,
    search_values_too: bool = False,
    use_regex: bool = False,
) -> Dict[str, Optional[str]]:
    """High-level search combining key and optionally value search.

    Args:
        secrets: Mapping of key -> value loaded from a vault.
        pattern: Search pattern.
        search_values_too: Also search inside values.
        use_regex: Treat *pattern* as a regular expression.

    Returns:
        Ordered dict of matching key -> value entries.
    """
    matched_keys = set(search_keys(secrets, pattern, use_regex=use_regex))
    if search_values_too:
        for k, _ in search_values(secrets, pattern, use_regex=use_regex):
            matched_keys.add(k)
    return {k: secrets[k] for k in sorted(matched_keys)}
