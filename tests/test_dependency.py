"""Tests for envault.dependency."""
import pytest
from envault.dependency import (
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    dependency_graph,
)


@pytest.fixture()
def secrets():
    return {"DB_URL": "postgres://", "DB_PASS": "s3cr3t", "API_KEY": "abc123"}


def test_add_dependency_creates_mapping(secrets):
    add_dependency(secrets, "DB_URL", "DB_PASS")
    assert "DB_PASS" in get_dependencies(secrets, "DB_URL")


def test_add_dependency_multiple(secrets):
    add_dependency(secrets, "DB_URL", "DB_PASS")
    add_dependency(secrets, "DB_URL", "API_KEY")
    deps = get_dependencies(secrets, "DB_URL")
    assert "DB_PASS" in deps
    assert "API_KEY" in deps


def test_add_dependency_duplicate_is_idempotent(secrets):
    add_dependency(secrets, "DB_URL", "DB_PASS")
    add_dependency(secrets, "DB_URL", "DB_PASS")
    assert get_dependencies(secrets, "DB_URL").count("DB_PASS") == 1


def test_add_dependency_missing_key_raises(secrets):
    with pytest.raises(KeyError):
        add_dependency(secrets, "MISSING", "DB_PASS")


def test_add_dependency_missing_depends_on_raises(secrets):
    with pytest.raises(KeyError):
        add_dependency(secrets, "DB_URL", "MISSING")


def test_add_dependency_self_raises(secrets):
    with pytest.raises(ValueError):
        add_dependency(secrets, "DB_URL", "DB_URL")


def test_remove_dependency(secrets):
    add_dependency(secrets, "DB_URL", "DB_PASS")
    remove_dependency(secrets, "DB_URL", "DB_PASS")
    assert get_dependencies(secrets, "DB_URL") == []


def test_remove_nonexistent_dependency_raises(secrets):
    with pytest.raises(KeyError):
        remove_dependency(secrets, "DB_URL", "DB_PASS")


def test_get_dependents_reverse_lookup(secrets):
    add_dependency(secrets, "DB_URL", "DB_PASS")
    add_dependency(secrets, "API_KEY", "DB_PASS")
    rdeps = get_dependents(secrets, "DB_PASS")
    assert "DB_URL" in rdeps
    assert "API_KEY" in rdeps


def test_get_dependents_empty_when_none(secrets):
    assert get_dependents(secrets, "DB_PASS") == []


def test_dependency_graph_returns_all(secrets):
    add_dependency(secrets, "DB_URL", "DB_PASS")
    graph = dependency_graph(secrets)
    assert "DB_URL" in graph
    assert "DB_PASS" in graph["DB_URL"]


def test_dependency_graph_empty_when_no_deps(secrets):
    assert dependency_graph(secrets) == {}
