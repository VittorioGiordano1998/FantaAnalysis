"""Lettura del listone completo dall'Excel versionato (layer data).

`resources/listone.xlsx` è la copia versionata del listone dell'utente
(ruoli Mantra, squadra, titolarità, FMV, rigorista, punizioni, angoli,
presi): a differenza delle cache CSV in `data/` non è rigenerabile, per
questo vive in `resources/` e si aggiorna ricopiando il file dell'utente.

Nessuna rete: il parsing è una funzione pura testabile contro file
generati in `tmp_path`.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from entities import ListoneRow, Role

logger = logging.getLogger(__name__)

LISTONE_PATH = Path("resources") / "listone.xlsx"

# Versione dello schema di parsing: rileva i deploy misti (fetch_listone.py
# vecchio servito con main.py nuovo → colonne booleane invece delle priorità).
LISTONE_PARSER_VERSION = 2

# Hash SHA-256 del file `resources/listone.xlsx` committato: rileva i deploy
# che servono un listone stantio (giocatori rimossi/aggiunti). Va aggiornato
# ogni volta che si ricopia il file dell'utente nel repo.
LISTONE_FILE_SHA256 = "0bc4a87bf373e7f3460fd695e3ff9a412ef46a7ffa13601d411b13ccac49b680"

_ROLE_COLUMNS = (
    ("P", Role.POR),
    ("Ds", Role.DS),
    ("B", Role.B),
    ("Dc", Role.DC),
    ("Dd", Role.DD),
    ("E", Role.E),
    ("M", Role.M),
    ("C", Role.C),
    ("T", Role.T),
    ("W", Role.W),
    ("A", Role.A),
    ("Pc", Role.PC),
)

_CHECK_COLUMN = "✔"


def read_listone(path: Path | None = None) -> tuple[ListoneRow, ...]:
    """Legge il listone Excel e lo mappa sulle entità condivise.

    Args:
        path: percorso del file (default `LISTONE_PATH`).

    Returns:
        Le righe del listone nell'ordine del file; vuota se il file non
        esiste ancora (primo avvio o test).
    """
    path = path or LISTONE_PATH
    if not path.is_file():
        logger.warning("Listone assente: %s (copialo in resources/ e committa)", path)
        return ()
    frame = pd.read_excel(path)
    rows: list[ListoneRow] = []
    for _, raw in frame.iterrows():
        name = _cell(raw, "Giocatore")
        if not name:
            continue
        rows.append(
            ListoneRow(
                name=name,
                team_name=_cell(raw, "Squadra"),
                roles=tuple(role for column, role in _ROLE_COLUMNS if _flagged(raw, column)),
                titolarita=_optional_float(raw, "Titolarità"),
                fmv=_optional_float(raw, "FMV"),
                rigorista=_optional_int(raw, "Rigorista"),
                punizioni=_optional_int(raw, "Punizioni"),
                angoli=_optional_int(raw, "Angoli"),
                preso_noi=_optional_bool(raw, "Preso Noi"),
                preso_altri=_optional_bool(raw, "Preso Altri"),
            )
        )
    return tuple(rows)


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
