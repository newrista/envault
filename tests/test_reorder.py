"""Tests for envault.reorder."""

import pytest

from envault.reorder import apply_order, move_to_bottom, move_to_top, sort_secrets


@pytest.fixture()
def secrets():
    return {
        "ZEBRA": "z",
        "ALPHA": "a",
        "MANGO": "m",
        "__meta": "internal",
        "__rotation": "data",
    }


# ---------------------------------------------------------------------------
# sort_secrets
# ---------------------------------------------------------------------------


def test_sort_secrets_alphabetical(secrets):
    result = sort_secrets(secrets)
    user_keys = [k for k in result if not k.startswith("__")]
    assert user_keys == sorted(user_keys, key=str.lower)


def test_sort_secrets_reverse(secrets):
    result = sort_secrets(secrets, reverse=True)
    user_keys = [k for k in result if not k.startswith("__")]
    assert user_keys == sorted(user_keys, key=str.lower, reverse=True)


def test_sort_secrets_internal_keys_preserved_at_end(secrets):
    result = sort_secrets(secrets)
    keys = list(result.keys())
    internal_indices = [i for i, k in enumerate(keys) if k.startswith("__")]
    user_indices = [i for i, k in enumerate(keys) if not k.startswith("__")]
    assert all(u < i for u in user_indices for i in internal_indices)


def test_sort_secrets_values_preserved(secrets):
    result = sort_secrets(secrets)
    for k, v in secrets.items():
        assert result[k] == v


def test_sort_secrets_case_sensitive():
    data = {"banana": "1", "Apple": "2", "cherry": "3"}
    result = sort_secrets(data, case_sensitive=True)
    user_keys = list(result.keys())
    assert user_keys == sorted(user_keys)


# ---------------------------------------------------------------------------
# move_to_top
# ---------------------------------------------------------------------------


def test_move_to_top_places_key_first(secrets):
    result = move_to_top(secrets, ["ZEBRA"])
    assert list(result.keys())[0] == "ZEBRA"


def test_move_to_top_multiple_keys_in_order(secrets):
    result = move_to_top(secrets, ["MANGO", "ALPHA"])
    keys = list(result.keys())
    assert keys[0] == "MANGO"
    assert keys[1] == "ALPHA"


def test_move_to_top_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="MISSING"):
        move_to_top(secrets, ["MISSING"])


def test_move_to_top_internal_key_raises(secrets):
    with pytest.raises(ValueError, match="internal"):
        move_to_top(secrets, ["__meta"])


# ---------------------------------------------------------------------------
# move_to_bottom
# ---------------------------------------------------------------------------


def test_move_to_bottom_places_key_before_internals(secrets):
    result = move_to_bottom(secrets, ["ALPHA"])
    keys = list(result.keys())
    internal_start = next(i for i, k in enumerate(keys) if k.startswith("__"))
    alpha_index = keys.index("ALPHA")
    assert alpha_index < internal_start
    # ALPHA should be the last user key
    user_keys = [k for k in keys if not k.startswith("__")]
    assert user_keys[-1] == "ALPHA"


def test_move_to_bottom_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        move_to_bottom(secrets, ["NOPE"])


def test_move_to_bottom_internal_key_raises(secrets):
    with pytest.raises(ValueError):
        move_to_bottom(secrets, ["__rotation"])


# ---------------------------------------------------------------------------
# apply_order
# ---------------------------------------------------------------------------


def test_apply_order_respects_explicit_order(secrets):
    result = apply_order(secrets, ["MANGO", "ZEBRA", "ALPHA"])
    user_keys = [k for k in result if not k.startswith("__")]
    assert user_keys == ["MANGO", "ZEBRA", "ALPHA"]


def test_apply_order_appends_unlisted_keys(secrets):
    result = apply_order(secrets, ["MANGO"])
    user_keys = [k for k in result if not k.startswith("__")]
    assert user_keys[0] == "MANGO"
    assert set(user_keys) == {"MANGO", "ZEBRA", "ALPHA"}


def test_apply_order_missing_key_raises(secrets):
    with pytest.raises(KeyError, match="GHOST"):
        apply_order(secrets, ["GHOST"])


def test_apply_order_internal_key_raises(secrets):
    with pytest.raises(ValueError):
        apply_order(secrets, ["__meta"])


def test_apply_order_values_unchanged(secrets):
    result = apply_order(secrets, ["ALPHA", "MANGO", "ZEBRA"])
    for k, v in secrets.items():
        assert result[k] == v
