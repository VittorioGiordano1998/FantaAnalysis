"""Smoke test di boot delle pagine Streamlit (niente rete, niente disco).

Esegue `main.py` e le pagine con cache assente e funzioni di fetch patchate:
un'eccezione al boot (es. ImportError in un import) fa fallire il test.
Riproduce l'ambiente Cloud all'avvio: `data/` vuota, nessuna chiamata di
rete, nessun filesystem reale.
"""

from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

import fetch_fixtures as ff
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
    empty = pd.DataFrame()
    monkeypatch.setattr(fq, "get_quotazioni", lambda force_refresh=False, **kw: empty)
    monkeypatch.setattr(fs, "get_statistiche", lambda force_refresh=False, **kw: empty)
    monkeypatch.setattr(ff, "get_calendario", lambda force_refresh=False, **kw: empty)


@pytest.mark.parametrize("script", PAGES)
def test_page_boots_without_exception(script):
    at = AppTest.from_file(script).run()
    assert not at.exception, f"{script}: {at.exception}"
