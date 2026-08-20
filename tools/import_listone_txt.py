"""Converte `ListoneAggiornato.txt` (export rosa completa) → `resources/listone.xlsx`.

Replica le stesse colonne e convenzioni di `convert_listone.py`:
- ruoli Mantra con spunta "✔" (ordine colonne del listone);
- titolarità % e FMV come float;
- per i giocatori già presenti in `listone.json` preserva i campi che il .txt
  non trasporta: Rigorista, Punizioni, Angoli, Preso Noi, Preso Altri.

Poi va rilanciato `python tools/convert_listone.py` per rigenerare il JSON.

Usage:
    python tools/import_listone_txt.py [--input resources/listone_aggiornato.txt]
                                       [--reference web/src/data/listone.json]
                                       [--output resources/listone.xlsx]
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

import pandas as pd

from convert_listone import _CHECK_COLUMN, _ROLE_COLUMNS

logger = logging.getLogger(__name__)

DEFAULT_INPUT = Path("resources") / "listone_aggiornato.txt"
DEFAULT_REFERENCE = Path("src") / "data" / "listone.json"
DEFAULT_OUTPUT = Path("resources") / "listone.xlsx"

_ROLE_CODES = {column for column, _ in _ROLE_COLUMNS}

_TIT_RE = re.compile(r"^\d+(\.\d+)?%$")
_NUM_RE = re.compile(r"^\d+(\.\d+)?$")


def parse_txt(path: Path) -> list[dict]:
    """Parsa il .txt in giocatori: {name, team, roles, titolarita, fmv}."""
    players: list[dict] = []
    team: str | None = None
    roles: list[str] = []
    name: str | None = None
    titolarita: float | None = None
    mv: float | None = None
    fmv: float | None = None
    expect: str = ""

    def flush() -> None:
        nonlocal roles, name, titolarita, mv, fmv
        if name is not None:
            players.append(
                {
                    "name": name,
                    "team": team or "",
                    "roles": list(roles),
                    "titolarita": titolarita,
                    "fmv": fmv,
                }
            )
        roles = []
        name = None
        titolarita = None
        mv = None
        fmv = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("rosa completa"):
            flush()
            team = line.split(" ", 2)[-1]
            continue
        if line == "Immagine giocatore":
            flush()
            continue
        if name is None:
            if line in _ROLE_CODES:
                roles.append(line)
                continue
            name = line
            continue
        if _TIT_RE.match(line) and titolarita is None:
            titolarita = float(line[:-1])
            continue
        if line in {"Titolarità", "PMA"}:
            continue
        if line == "MV":
            expect = "mv"
            continue
        if line == "FMV":
            expect = "fmv"
            continue
        if _NUM_RE.match(line):
            if expect == "mv" and mv is None:
                mv = float(line)
                expect = ""
            elif expect == "fmv" and fmv is None:
                fmv = float(line)
                expect = ""
    flush()
    return players


def load_reference(path: Path) -> dict[tuple[str, str], dict]:
    """Indice del JSON attuale: (nome, squadra) → record."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {(p["name"], p["teamName"]): p for p in payload["players"]}


def build_frame(players: list[dict], reference: dict[tuple[str, str], dict]) -> pd.DataFrame:
    """Costruisce il DataFrame nelle stesse colonne/ordine di convert_listone.py."""
    columns = [column for column, _ in _ROLE_COLUMNS]
    rows: list[dict] = []
    for p in players:
        ref = reference.get((p["name"], p["team"]), {})
        row: dict = {
            "Giocatore": p["name"],
            "Squadra": p["team"],
            "Titolarità": p["titolarita"],
            "FMV": p["fmv"],
            "Rigorista": ref.get("rigorista"),
            "Punizioni": ref.get("punizioni"),
            "Angoli": ref.get("angoli"),
            "Preso Noi": bool(ref.get("presoNoi", False)),
            "Preso Altri": bool(ref.get("presoAltri", False)),
        }
        for column, _ in _ROLE_COLUMNS:
            row[column] = _CHECK_COLUMN if column in p["roles"] else None
        rows.append(row)

    ordered = ["Giocatore", *columns, "Squadra", "Titolarità", "FMV",
               "Rigorista", "Punizioni", "Angoli", "Preso Noi", "Preso Altri"]
    return pd.DataFrame(rows, columns=ordered)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Export .txt aggiornato")
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE, help="JSON attuale")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="XLSX di destinazione")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    players = parse_txt(args.input)
    reference = load_reference(args.reference)
    frame = build_frame(players, reference)
    frame.to_excel(args.output, index=False)
    logger.info("Scritti %d giocatori in %s", len(frame), args.output)
    print(f"{len(frame)} giocatori -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())