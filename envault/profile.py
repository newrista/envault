"""Profile management: named collections of keys for environment-specific exports."""

from __future__ import annotations

from typing import Dict, List

PROFILE_META_KEY = "__profiles__"


def _get_profiles(secrets: dict) -> Dict[str, List[str]]:
    """Return the profiles index stored inside the secrets dict."""
    return secrets.get(PROFILE_META_KEY, {})


def _set_profiles(secrets: dict, profiles: Dict[str, List[str]]) -> None:
    """Persist the profiles index back into the secrets dict."""
    secrets[PROFILE_META_KEY] = profiles


def create_profile(secrets: dict, name: str) -> None:
    """Create an empty profile. Idempotent if it already exists."""
    profiles = _get_profiles(secrets)
    if name not in profiles:
        profiles[name] = []
        _set_profiles(secrets, profiles)


def delete_profile(secrets: dict, name: str) -> None:
    """Delete a profile by name. Raises KeyError if not found."""
    profiles = _get_profiles(secrets)
    if name not in profiles:
        raise KeyError(f"Profile '{name}' does not exist.")
    del profiles[name]
    _set_profiles(secrets, profiles)


def add_key_to_profile(secrets: dict, name: str, key: str) -> None:
    """Add a secret key to a profile. Raises if profile or key is missing."""
    profiles = _get_profiles(secrets)
    if name not in profiles:
        raise KeyError(f"Profile '{name}' does not exist.")
    if key not in secrets:
        raise KeyError(f"Secret key '{key}' does not exist in vault.")
    if key not in profiles[name]:
        profiles[name].append(key)
        _set_profiles(secrets, profiles)


def remove_key_from_profile(secrets: dict, name: str, key: str) -> None:
    """Remove a key from a profile. Raises if profile not found or key not in profile."""
    profiles = _get_profiles(secrets)
    if name not in profiles:
        raise KeyError(f"Profile '{name}' does not exist.")
    if key not in profiles[name]:
        raise KeyError(f"Key '{key}' is not in profile '{name}'.")
    profiles[name].remove(key)
    _set_profiles(secrets, profiles)


def get_profile_keys(secrets: dict, name: str) -> List[str]:
    """Return the list of keys belonging to a profile."""
    profiles = _get_profiles(secrets)
    if name not in profiles:
        raise KeyError(f"Profile '{name}' does not exist.")
    return list(profiles[name])


def list_profiles(secrets: dict) -> List[str]:
    """Return all profile names."""
    return list(_get_profiles(secrets).keys())


def resolve_profile(secrets: dict, name: str) -> Dict[str, str]:
    """Return a dict of key→value pairs for all keys in the profile."""
    keys = get_profile_keys(secrets, name)
    return {k: secrets[k] for k in keys if k in secrets}
