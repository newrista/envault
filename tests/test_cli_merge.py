"""Tests for envault.cli_merge."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from envault.cli_merge import merge_group
from envault.vault import Vault

PASSWORD = "test-pass"


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def src_vault(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    v = Vault(str(d))
    v.save({"SRC_ONLY": "from_src", "SHARED": "src_value"}, PASSWORD)
    return str(d)


@pytest.fixture()
def dst_vault(tmp_path):
    d = tmp_path / "dst"
    d.mkdir()
    v = Vault(str(d))
    v.save({"SHARED": "dst_value", "DST_ONLY": "from_dst"}, PASSWORD)
    return str(d)


def _invoke(runner, src, dst, extra=None):
    args = [
        "run", src, dst,
        "--src-password", PASSWORD,
        "--dst-password", PASSWORD,
    ]
    if extra:
        args.extend(extra)
    return runner.invoke(merge_group, args, catch_exceptions=False)


def test_merge_adds_new_key(runner, src_vault, dst_vault):
    result = _invoke(runner, src_vault, dst_vault)
    assert result.exit_code == 0
    assert "SRC_ONLY" in result.output
    v = Vault(dst_vault)
    secrets = v.load(PASSWORD)
    assert secrets["SRC_ONLY"] == "from_src"


def test_merge_keep_does_not_overwrite(runner, src_vault, dst_vault):
    _invoke(runner, src_vault, dst_vault, ["--strategy", "keep"])
    v = Vault(dst_vault)
    secrets = v.load(PASSWORD)
    assert secrets["SHARED"] == "dst_value"


def test_merge_overwrite_replaces_shared_key(runner, src_vault, dst_vault):
    result = _invoke(runner, src_vault, dst_vault, ["--strategy", "overwrite"])
    assert result.exit_code == 0
    v = Vault(dst_vault)
    secrets = v.load(PASSWORD)
    assert secrets["SHARED"] == "src_value"


def test_merge_dry_run_does_not_write(runner, src_vault, dst_vault):
    _invoke(runner, src_vault, dst_vault, ["--dry-run"])
    v = Vault(dst_vault)
    secrets = v.load(PASSWORD)
    # SRC_ONLY should NOT be present because dry-run was used
    assert "SRC_ONLY" not in secrets


def test_merge_missing_src_vault_errors(runner, tmp_path, dst_vault):
    result = runner.invoke(
        merge_group,
        ["run", str(tmp_path / "nope"), dst_vault,
         "--src-password", PASSWORD, "--dst-password", PASSWORD],
        catch_exceptions=False,
    )
    assert result.exit_code != 0
    assert "Source vault not found" in result.output
