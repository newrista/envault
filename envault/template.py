"""Template rendering for environment variable substitution."""

import re
from typing import Dict, Optional


class TemplateMissingKeyError(KeyError):
    """Raised when a referenced key is not found in secrets."""


def render(template: str, secrets: Dict[str, str], strict: bool = True) -> str:
    """Render a template string substituting {{KEY}} placeholders with secret values.

    Args:
        template: A string containing {{KEY}} placeholders.
        secrets: A dict of secret key/value pairs.
        strict: If True, raise TemplateMissingKeyError for unknown keys.
                If False, leave unresolved placeholders unchanged.

    Returns:
        Rendered string with placeholders replaced.
    """
    pattern = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")

    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key in secrets:
            return secrets[key]
        if strict:
            raise TemplateMissingKeyError(
                f"Template references unknown key: '{key}'"
            )
        return match.group(0)

    return pattern.sub(replace, template)


def list_placeholders(template: str) -> list[str]:
    """Return a list of unique placeholder keys found in a template string."""
    pattern = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")
    seen: list[str] = []
    for match in pattern.finditer(template):
        key = match.group(1)
        if key not in seen:
            seen.append(key)
    return seen


def render_dict(
    templates: Dict[str, str],
    secrets: Dict[str, str],
    strict: bool = True,
) -> Dict[str, str]:
    """Render every value in a dict of templates using the provided secrets."""
    return {k: render(v, secrets, strict=strict) for k, v in templates.items()}


def validate_template(template: str, secrets: Dict[str, str]) -> list[str]:
    """Return a list of placeholder keys in the template that are missing from secrets.

    Useful for pre-flight checks before rendering, allowing callers to report
    all missing keys at once rather than failing on the first missing key.

    Args:
        template: A string containing {{KEY}} placeholders.
        secrets: A dict of secret key/value pairs.

    Returns:
        A list of keys referenced in the template but absent from secrets.
        An empty list means the template can be rendered without errors.
    """
    return [key for key in list_placeholders(template) if key not in secrets]
