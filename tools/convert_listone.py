"""Converte `resources/listone.xlsx` → `web/src/data/listone.json`.

Replica esattamente `fetch_listone.read_listone` (stesso schema, stesse soglie):
- ruoli Mantra per spunta (ordine del file), multiruolo incluso;
- titolarità % e FMV come float o null;
- priorità rigorista/punizioni/angoli 1/2/3, vecchia spunta "✔" → 3;
- righe vuote in coda escluse (campo "Giocatore" vuoto).

Output: JSON deterministico in `web/src/data/listone.json` (unica fonte del
web). Quando l'utente aggiorna `Listone.xlsx` basta rilanciare questo script e
committare il JSON nuovo.

Usage:
    python tools/convert_listone.py [--input resources/listone.xlsx]
                                    [--output web/src/data/listone.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_INPUT = Path("resources") / "listone.xlsx"
DEFAULT_OUTPUT = Path("web") / "src" / "data" / "listone.json"
OUTPUT_SCHEMA_VERSION = 1

_ROLE_COLUMNS = (
    ("P", "por"),
    ("Ds", "ds"),
    ("B", "b"),
    ("Dc", "dc"),
    ("Dd", "dd"),
    ("E", "e"),
    ("M", "m"),
    ("C", "c"),
    ("T", "t"),
    ("W", "w"),
    ("A", "a"),
    ("Pc", "pc"),
)

_CHECK_COLUMN = "✔"


def _cell(row: pd.Series, column: str) -> str:
    """Testo di una cella, vuoto se assente o NaN."""
    value = row.get(column)
    return "" if pd.isna(value) else str(value).strip()


def _flagged(row: pd.Series, column: str) -> bool:
    """True se la cella contiene la spunta del listone."""
    return _cell(row, column) == _CHECK_COLUMN


def _optional_float(row: pd.Series, column: str) -> float | None:
    """Valore numerico opzionale (None per celle vuote/NaN)."""
    value = row.get(column)
    return None if pd.isna(value) else float(value)


def _optional_int(row: pd.Series, column: str) -> int | None:
    """Priorità numerica opzionale (1, 2, 3, ...; None se vuota).

    La vecchia spunta "✔" del listone viene trattata come priorità 3.
    """
    value = row.get(column)
    if pd.isna(value):
        return None
    if str(value).strip() == _CHECK_COLUMN:
        return 3
    return int(value)


def _optional_bool(row: pd.Series, column: str) -> bool:
    """Valore booleano (False per celle vuote/NaN)."""
    value = row.get(column)
    return False if pd.isna(value) else bool(value)


def read_listone(path: Path) -> dict:
    """Legge l'Excel e mappa le righe sul payload JSON del web (ListoneRow).

    Args:
        path: percorso del file `.xlsx`.

    Returns:
        Il payload versionato `{"version", "players"}` con le righe nell'ordine
        del file.
    """
    frame = pd.read_excel(path)
    players: list[dict] = []
    for _, raw in frame.iterrows():
        name = _cell(raw, "Giocatore")
        if not name:
            continue
        players.append(
            {
                "name": name,
                "teamName": _cell(raw, "Squadra"),
                "roles": [role for column, role in _ROLE_COLUMNS if _flagged(raw, column)],
                "titolarita": _optional_float(raw, "Titolarità"),
                "fmv": _optional_float(raw, "FMV"),
                "rigorista": _optional_int(raw, "Rigorista"),
                "punizioni": _optional_int(raw, "Punizioni"),
                "angoli": _optional_int(raw, "Angoli"),
                "presoNoi": _optional_bool(raw, "Preso Noi"),
                "presoAltri": _optional_bool(raw, "Preso Altri"),
            }
        )
    return {"version": OUTPUT_SCHEMA_VERSION, "players": players}


def convert(input_path: Path, output_path: Path) -> int:
    """Esegue la conversione e scrive il JSON (deterministico, utf-8).

    Args:
        input_path: Excel del listone.
        output_path: JSON di destinazione.

    Returns:
        Numero di giocatori scritti.
    """
    payload = read_listone(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    logger.info(
        "Scritti %d giocatori in %s (sha256 %s)", len(payload["players"]), output_path, digest
    )
    return len(payload["players"])


def main() -> int:
    """Entry point CLI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Excel del listone")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="JSON di destinazione")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    count = convert(args.input, args.output)
    print(f"{count} giocatori -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
