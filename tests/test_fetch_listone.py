"""Test del parser del listone Excel (layer data, niente rete/niente disco).

Usa file generati in `tmp_path`: nessun filesystem reale.
"""

from pathlib import Path

import pandas as pd

from entities import Role
from fetch_listone import read_listone


def _write_listone(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_excel(path, index=False)
    return path


def test_read_listone_maps_all_columns(tmp_path):
    path = _write_listone(
        tmp_path / "listone.xlsx",
        [
            {
                "Giocatore": "Carnesecchi",
                "P": "✔",
                "Ds": "",
                "B": "",
                "Dc": "",
                "Dd": "",
                "E": "",
                "M": "",
                "C": "",
                "T": "",
                "W": "",
                "A": "",
                "Pc": "",
                "Squadra": "Atalanta",
                "Titolarità": 95.0,
                "FMV": 5.58,
                "Rigorista": 2,
                "Punizioni": 1,
                "Angoli": "",
                "Preso Noi": False,
                "Preso Altri": False,
            },
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
                "Rigorista": 1,
                "Punizioni": "",
                "Angoli": "✔",
                "Preso Noi": True,
                "Preso Altri": True,
            },
        ],
    )
    rows = read_listone(path)
    assert len(rows) == 2

    keeper = rows[0]
    assert keeper.name == "Carnesecchi"
    assert keeper.team_name == "Atalanta"
    assert keeper.roles == (Role.POR,)
    assert keeper.titolarita == 95.0
    assert keeper.fmv == 5.58
    assert keeper.rigorista == 2 and keeper.punizioni == 1 and keeper.angoli is None
    assert not keeper.preso_noi and not keeper.preso_altri

    wing = rows[1]
    assert wing.roles == (Role.E, Role.W)
    assert wing.titolarita is None and wing.fmv is None
    assert wing.rigorista == 1 and wing.punizioni is None and wing.angoli == 1
    assert wing.preso_noi and wing.preso_altri


def test_read_listone_multiruolo_order_follows_file_columns(tmp_path):
    path = _write_listone(
        tmp_path / "listone.xlsx",
        [
            {
                "Giocatore": "McTominay",
                "P": "",
                "Ds": "",
                "B": "",
                "Dc": "",
                "Dd": "",
                "E": "",
                "M": "",
                "C": "✔",
                "T": "✔",
                "W": "",
                "A": "",
                "Pc": "",
                "Squadra": "Napoli",
                "Titolarità": None,
                "FMV": None,
                "Rigorista": "",
                "Punizioni": "",
                "Angoli": "",
                "Preso Noi": False,
                "Preso Altri": False,
            }
        ],
    )
    rows = read_listone(path)
    assert rows[0].roles == (Role.C, Role.T)


def test_read_listone_empty_rows_are_skipped(tmp_path):
    rows = [
        {
            "Giocatore": "Zappacosta",
            "P": "",
            "Ds": "",
            "B": "",
            "Dc": "",
            "Dd": "✔",
            "E": "✔",
            "M": "",
            "C": "",
            "T": "",
            "W": "",
            "A": "",
            "Pc": "",
            "Squadra": "Atalanta",
            "Titolarità": None,
            "FMV": None,
            "Rigorista": "",
            "Punizioni": "",
            "Angoli": "",
            "Preso Noi": None,
            "Preso Altri": None,
        },
        {"Giocatore": None},
    ]
    path = _write_listone(tmp_path / "listone.xlsx", rows)
    assert len(read_listone(path)) == 1


def test_read_listone_missing_file_returns_empty(tmp_path):
    assert read_listone(tmp_path / "assente.xlsx") == ()


def test_read_listone_empty_preso_cells_are_false(tmp_path):
    path = _write_listone(
        tmp_path / "listone.xlsx",
        [
            {
                "Giocatore": "Zappacosta",
                "P": "",
                "Ds": "",
                "B": "",
                "Dc": "",
                "Dd": "✔",
                "E": "✔",
                "M": "",
                "C": "",
                "T": "",
                "W": "",
                "A": "",
                "Pc": "",
                "Squadra": "Atalanta",
                "Titolarità": None,
                "FMV": None,
                "Rigorista": "",
                "Punizioni": "",
                "Angoli": "",
                "Preso Noi": None,
                "Preso Altri": None,
            }
        ],
    )
    rows = read_listone(path)
    assert not rows[0].preso_noi and not rows[0].preso_altri
