"""Tests for envault.cascade module."""

from __future__ import annotations

import pytest

from envault.cascade import CascadeResult, cascade_resolve, list_overrides


LAYER_BASE = ("base", {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_ENV": "dev"})
LAYER_STAGING = ("staging", {"DB_HOST": "staging.db", "APP_ENV": "staging"})
LAYER_PROD = ("prod", {"DB_HOST": "prod.db", "APP_ENV": "production", "NEW_KEY": "hello"})


# ---------------------------------------------------------------------------
# cascade_resolve
# ---------------------------------------------------------------------------

def test_cascade_resolve_empty_layers_returns_empty():
    result = cascade_resolve([])
    assert result.resolved == {}
    assert result.sources == {}


def test_cascade_resolve_single_layer():
    result = cascade_resolve([LAYER_BASE])
    assert result.resolved["DB_HOST"] == "localhost"
    assert result.sources["DB_HOST"] == "base"


def test_cascade_higher_priority_overrides_lower():
    result = cascade_resolve([LAYER_BASE, LAYER_STAGING])
    assert result.resolved["DB_HOST"] == "staging.db"
    assert result.sources["DB_HOST"] == "staging"


def test_cascade_lower_priority_key_preserved_when_not_overridden():
    result = cascade_resolve([LAYER_BASE, LAYER_STAGING])
    assert result.resolved["DB_PORT"] == "5432"
    assert result.sources["DB_PORT"] == "base"


def test_cascade_three_layers_highest_wins():
    result = cascade_resolve([LAYER_BASE, LAYER_STAGING, LAYER_PROD])
    assert result.resolved["DB_HOST"] == "prod.db"
    assert result.resolved["APP_ENV"] == "production"


def test_cascade_new_key_from_higher_layer_included():
    result = cascade_resolve([LAYER_BASE, LAYER_PROD])
    assert "NEW_KEY" in result.resolved
    assert result.resolved["NEW_KEY"] == "hello"


def test_cascade_internal_keys_excluded():
    layer = ("internal", {"__meta": "hidden", "REAL": "value"})
    result = cascade_resolve([layer])
    assert "__meta" not in result.resolved
    assert "REAL" in result.resolved


def test_cascade_filter_by_specific_keys():
    result = cascade_resolve([LAYER_BASE, LAYER_STAGING], keys=["DB_HOST"])
    assert list(result.resolved.keys()) == ["DB_HOST"]


def test_cascade_filter_by_keys_missing_in_all_layers():
    result = cascade_resolve([LAYER_BASE], keys=["NONEXISTENT"])
    assert result.resolved == {}


def test_cascade_result_repr_contains_keys():
    result = cascade_resolve([LAYER_BASE])
    assert isinstance(result, CascadeResult)


# ---------------------------------------------------------------------------
# list_overrides
# ---------------------------------------------------------------------------

def test_list_overrides_detects_overridden_key():
    overrides = list_overrides([LAYER_BASE, LAYER_STAGING])
    assert "DB_HOST" in overrides
    assert len(overrides["DB_HOST"]) == 2


def test_list_overrides_excludes_unique_keys():
    overrides = list_overrides([LAYER_BASE, LAYER_PROD])
    assert "DB_PORT" not in overrides  # only in base
    assert "NEW_KEY" not in overrides  # only in prod


def test_list_overrides_empty_when_no_shared_keys():
    a = ("a", {"KEY_A": "1"})
    b = ("b", {"KEY_B": "2"})
    overrides = list_overrides([a, b])
    assert overrides == {}


def test_list_overrides_excludes_internal_keys():
    a = ("a", {"__internal": "x"})
    b = ("b", {"__internal": "y"})
    overrides = list_overrides([a, b])
    assert "__internal" not in overrides


def test_list_overrides_preserves_order_low_to_high():
    overrides = list_overrides([LAYER_BASE, LAYER_STAGING, LAYER_PROD])
    paths = [path for path, _ in overrides["DB_HOST"]]
    assert paths == ["base", "staging", "prod"]
