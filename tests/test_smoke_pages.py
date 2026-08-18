"""Smoke test di boot delle pagine Streamlit (niente rete, niente disco).

Esegue `main.py` e le pagine con cache assente e funzioni di fetch patchate:
un'eccezione al boot (es. ImportError in un import) fa fallire il test.
Riproduce l'ambiente Cloud all'avvio: `data/` vuota, nessuna chiamata di
rete, nessun filesystem reale.
"""

from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import fetch_fixtures as ff
import fetch_listone as fl
import fetch_quotazioni as fq
import fetch_stats as fs
import state as st8

ROOT = Path(__file__).resolve().parent.parent
PAGES = (
    ROOT / "main.py",
    ROOT / "pages/RosaOttimale.py",
    ROOT / "pages/Analisi.py",
    ROOT / "pages/Guide.py",
)


@pytest.fixture(autouse=True)
def _empty_cache(monkeypatch, tmp_path):
    """Cache vuota e fetch inoffensivi per non toccare rete/disco."""
    monkeypatch.setattr(fq, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(fs, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(ff, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(st8, "STATE_FILE", tmp_path / "asta.json")
    monkeypatch.setattr(st8, "LISTONE_FLAGS_FILE", tmp_path / "listone_flags.json")
    monkeypatch.setattr(fl, "LISTONE_PATH", tmp_path / "listone.xlsx")
    empty = pd.DataFrame()
    monkeypatch.setattr(fq, "get_quotazioni", lambda force_refresh=False, **kw: empty)
    monkeypatch.setattr(fs, "get_statistiche", lambda force_refresh=False, **kw: empty)
    monkeypatch.setattr(ff, "get_calendario", lambda force_refresh=False, **kw: empty)


@pytest.mark.parametrize("script", PAGES)
def test_page_boots_without_exception(script):
    at = AppTest.from_file(script).run()
    assert not at.exception, f"{script}: {at.exception}"


def test_main_renders_listone_when_file_present(monkeypatch, tmp_path):
    pd.DataFrame(
        [
            {
                "Giocatore": "Dimarco",
                "P": "",
                "Ds": "",
                "B": "",
                "Dc": "",
                "Dd": "",
                "E": "✔",
                "M": "",
                "C": "",
                "T": "",
                "W": "✔",
                "A": "",
                "Pc": "",
                "Squadra": "Inter",
                "Titolarità": 75.0,
                "FMV": 6.2,
                "Rigorista": "",
                "Punizioni": "",
                "Angoli": "✔",
                "Preso Noi": False,
                "Preso Altri": False,
            }
        ]
    ).to_excel(tmp_path / "listone.xlsx", index=False)
    monkeypatch.setattr(fl, "LISTONE_PATH", tmp_path / "listone.xlsx")
    st.cache_data.clear()
    at = AppTest.from_file(ROOT / "main.py").run()
    assert not at.exception
    assert len(at.dataframe) == 1


def test_main_marks_taken_with_buttons(monkeypatch, tmp_path):
    pd.DataFrame(
        [
            {
                "Giocatore": "Dimarco",
                "P": "",
                "Ds": "",
                "B": "",
                "Dc": "",
                "Dd": "",
                "E": "✔",
                "M": "",
                "C": "",
                "T": "",
                "W": "✔",
                "A": "",
                "Pc": "",
                "Squadra": "Inter",
                "Titolarità": None,
                "FMV": None,
                "Rigorista": "",
                "Punizioni": "",
                "Angoli": "",
                "Preso Noi": False,
                "Preso Altri": False,
            }
        ]
    ).to_excel(tmp_path / "listone.xlsx", index=False)
    monkeypatch.setattr(fl, "LISTONE_PATH", tmp_path / "listone.xlsx")
    st.cache_data.clear()
    at = AppTest.from_file(ROOT / "main.py").run()
    assert len(at.button) == 2
    at.button(key="mark_noi").click()
    at.run()
    assert not at.exception
    assert at.session_state["listone_flags"] == {}


def test_merged_flag_prefers_session_then_excel():
    from main import _merged_flag

    assert _merged_flag(True, False, None) == "noi"
    assert _merged_flag(False, True, None) == "altri"
    assert _merged_flag(False, False, None) == ""
    assert _merged_flag(True, False, "") == ""
    assert _merged_flag(False, True, "noi") == "noi"


def test_toggle_flags_cycles_owner_and_release():
    from main import _toggle_flags

    flags: dict[str, str] = {}
    _toggle_flags(flags, ["Dimarco"], "noi")
    assert flags == {"Dimarco": "noi"}
    _toggle_flags(flags, ["Dimarco"], "noi")
    assert flags == {"Dimarco": ""}
    _toggle_flags(flags, ["Dimarco"], "altri")
    assert flags == {"Dimarco": "altri"}
    _toggle_flags(flags, ["Dimarco", "Zappacosta"], "noi")
    assert flags == {"Dimarco": "noi", "Zappacosta": "noi"}
