"""Test del controllo di coerenza del deploy (version.txt vs LOGIC_VERSION).

Nessuna rete, nessun filesystem reale: il file versione è in `tmp_path`.
"""

from main import deploy_ok
from utility import LOGIC_VERSION


def test_deploy_ok_with_matching_version(tmp_path):
    version_file = tmp_path / "version.txt"
    version_file.write_text(LOGIC_VERSION + "\n", encoding="utf-8")
    assert deploy_ok(version_file)


def test_deploy_ok_fails_on_mismatch(tmp_path):
    version_file = tmp_path / "version.txt"
    version_file.write_text("0.0.0\n", encoding="utf-8")
    assert not deploy_ok(version_file)


def test_deploy_ok_fails_without_file(tmp_path):
    assert not deploy_ok(tmp_path / "version.txt")
