"""Test del controllo di coerenza del deploy (version.txt vs LOGIC_VERSION).

Nessuna rete, nessun filesystem reale: versione e listone sono in `tmp_path`.
"""

import hashlib
from pathlib import Path

import fetch_listone
from main import deploy_ok
from utility import LOGIC_VERSION


def _matching_listone(tmp_path, monkeypatch) -> Path:
    """File listone in tmp_path coerente con l'hash atteso (monkeypatch)."""
    content = b"listone-di-prova"
    path = tmp_path / "listone.xlsx"
    path.write_bytes(content)
    monkeypatch.setattr(fetch_listone, "LISTONE_FILE_SHA256", hashlib.sha256(content).hexdigest())
    return path


def test_deploy_ok_with_matching_version(tmp_path, monkeypatch):
    version_file = tmp_path / "version.txt"
    version_file.write_text(LOGIC_VERSION + "\n", encoding="utf-8")
    listone_file = _matching_listone(tmp_path, monkeypatch)
    assert deploy_ok(version_file, listone_file)


def test_deploy_ok_fails_on_mismatch(tmp_path, monkeypatch):
    version_file = tmp_path / "version.txt"
    version_file.write_text("0.0.0\n", encoding="utf-8")
    listone_file = _matching_listone(tmp_path, monkeypatch)
    assert not deploy_ok(version_file, listone_file)


def test_deploy_ok_fails_without_file(tmp_path, monkeypatch):
    listone_file = _matching_listone(tmp_path, monkeypatch)
    assert not deploy_ok(tmp_path / "version.txt", listone_file)


def test_deploy_ok_fails_on_old_listone_parser(tmp_path, monkeypatch):
    version_file = tmp_path / "version.txt"
    version_file.write_text(LOGIC_VERSION + "\n", encoding="utf-8")
    listone_file = _matching_listone(tmp_path, monkeypatch)
    monkeypatch.setattr(fetch_listone, "LISTONE_PARSER_VERSION", 1)
    assert not deploy_ok(version_file, listone_file)


def test_deploy_ok_fails_on_stale_listone_file(tmp_path, monkeypatch):
    version_file = tmp_path / "version.txt"
    version_file.write_text(LOGIC_VERSION + "\n", encoding="utf-8")
    path = _matching_listone(tmp_path, monkeypatch)
    path.write_bytes(b"listone-stantio")
    assert not deploy_ok(version_file, path)


def test_deploy_ok_fails_on_missing_listone_file(tmp_path, monkeypatch):
    version_file = tmp_path / "version.txt"
    version_file.write_text(LOGIC_VERSION + "\n", encoding="utf-8")
    assert not deploy_ok(version_file, tmp_path / "assente.xlsx")
