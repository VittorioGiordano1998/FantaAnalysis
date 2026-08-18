"""Test del convertitore Excel → JSON web (niente rete/niente disco reale).

`tools/convert_listone.py` deve mappare lo stesso schema di
`fetch_listone.read_listone`, quindi i casi di test qui speculano su quelli di
`test_fetch_listone.py`.
"""

import json
from pathlib import Path

import pandas as pd

from tools.convert_listone import convert, read_listone


def _write_listone(path: Path, rows: list[dict]) -> Path:
    pd.DataFrame(rows).to_excel(path, index=False)
    return path


def _row(**overrides) -> dict:
    base = {
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
    base.update(overrides)
    return base


def test_read_listone_maps_to_web_payload(tmp_path):
    path = _write_listone(
        tmp_path / "listone.xlsx",
        [
            _row(
                Giocatore="Carnesecchi",
                P="✔",
                Dd="",
                E="",
                Squadra="Atalanta",
                Titolarità=95.0,
                FMV=5.58,
                Rigorista=2,
                Punizioni=1,
            ),
            _row(
                Giocatore="Dimarco",
                E="✔",
                Squadra="Inter",
                Rigorista=1,
                Angoli="✔",
                **{"Preso Noi": True, "Preso Altri": True},
            ),
        ],
    )
    payload = read_listone(path)
    assert payload["version"] == 1
    assert len(payload["players"]) == 2

    keeper, wing = payload["players"]
    assert keeper["name"] == "Carnesecchi"
    assert keeper["teamName"] == "Atalanta"
    assert keeper["roles"] == ["por"]
    assert keeper["titolarita"] == 95.0
    assert keeper["fmv"] == 5.58
    assert keeper["rigorista"] == 2 and keeper["punizioni"] == 1 and keeper["angoli"] is None
    assert not keeper["presoNoi"] and not keeper["presoAltri"]

    assert wing["roles"] == ["dd", "e"]
    assert wing["rigorista"] == 1 and wing["angoli"] == 3
    assert wing["presoNoi"] and wing["presoAltri"]


def test_convert_writes_json_deterministic(tmp_path):
    path = _write_listone(
        tmp_path / "listone.xlsx",
        [_row(), {"Giocatore": None}],  # riga vuota esclusa
    )
    out = tmp_path / "listone.json"
    count = convert(path, out)
    assert count == 1
    assert json.loads(out.read_text(encoding="utf-8"))["players"][0]["name"] == "Zappacosta"

    out2 = tmp_path / "listone2.json"
    convert(path, out2)
    assert out.read_bytes() == out2.read_bytes()
