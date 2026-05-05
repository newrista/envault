"""Integration tests for the deps CLI commands."""
import pytest
from click.testing import CliRunner
from envault.cli_dependency import deps_group
from envault.vault import Vault

PASSWORD = "testpass"


@pytest.fixture()
def vault_dir(tmp_path):
    v = Vault(str(tmp_path))
    secrets = {"DB_URL": "postgres://localhost", "DB_PASS": "hunter2", "API_KEY": "xyz"}
    v.save(secrets, PASSWORD)
    return str(tmp_path)


@pytest.fixture()
def runner():
    return CliRunner()


def _invoke(runner, vault_dir, *args):
    return runner.invoke(
        deps_group,
        ["--vault-dir", vault_dir, "--password", PASSWORD, *args],
        catch_exceptions=False,
    )


def test_add_dependency_succeeds(runner, vault_dir):
    result = _invoke(runner, vault_dir, "add", "DB_URL", "DB_PASS")
    assert result.exit_code == 0
    assert "DB_URL -> DB_PASS" in result.output


def test_add_dependency_missing_key_fails(runner, vault_dir):
    result = runner.invoke(
        deps_group,
        ["add", "--vault-dir", vault_dir, "--password", PASSWORD, "MISSING", "DB_PASS"],
    )
    assert result.exit_code != 0


def test_remove_dependency_succeeds(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "DB_URL", "DB_PASS")
    result = _invoke(runner, vault_dir, "remove", "DB_URL", "DB_PASS")
    assert result.exit_code == 0
    assert "Removed" in result.output


def test_show_displays_deps_and_dependents(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "DB_URL", "DB_PASS")
    result = _invoke(runner, vault_dir, "show", "DB_PASS")
    assert result.exit_code == 0
    assert "DB_URL" in result.output  # DB_URL depends on DB_PASS


def test_graph_shows_no_deps_message(runner, vault_dir):
    result = _invoke(runner, vault_dir, "graph")
    assert result.exit_code == 0
    assert "No dependencies" in result.output


def test_graph_shows_defined_deps(runner, vault_dir):
    _invoke(runner, vault_dir, "add", "DB_URL", "DB_PASS")
    result = _invoke(runner, vault_dir, "graph")
    assert result.exit_code == 0
    assert "DB_URL" in result.output
    assert "DB_PASS" in result.output
