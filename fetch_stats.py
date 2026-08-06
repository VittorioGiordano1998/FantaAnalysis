"""Scraping delle statistiche stagionali Fantacalcio.it con cache CSV settimanale.

Modulo del layer `data`: tutto l'I/O di rete e file vive qui. La pagina
`/statistiche-serie-a` rende server-side una tabella `#stats` con tutti i
giocatori del listone (paginazione client-side); un solo GET basta.

Nota: i minuti giocati non sono esposti da Fantacalcio.it (vedi
KI-1-minuti-giocati-non-disponibili).
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from entities import SeasonStats
from fetch_common import (
    fetch_html,
    is_cache_fresh,
    read_cache_frame,
    to_decimal,
    to_int,
    write_csv,
)

logger = logging.getLogger(__name__)

STATISTICHE_URL = "https://www.fantacalcio.it/statistiche-serie-a"

CACHE_DIR = Path("data")
CACHE_FILE = CACHE_DIR / "statistiche.csv"
CACHE_MAX_AGE_DAYS = 7

CSV_COLUMNS = (
    "season",
    "name",
    "role",
    "role_label",
    "team_id",
    "team_code",
    "played_matches",
    "grade_avg",
    "fanta_avg",
    "goals",
    "goals_against",
    "penalties_scored",
    "penalties_total",
    "penalties_saved",
    "assists",
    "yellow_cards",
    "red_cards",
    "player_url",
)

_PLAYER_ROW_SELECTOR = "#stats tbody tr.player-row"
_ROLE_SPAN_SELECTOR = "span.role-mantra"
_SEASON_SELECTOR = "select#season option[selected]"


@dataclass(frozen=True)
class PlayerStatsRow:
    """Statistiche stagionali di un giocatore (una riga della tabella)."""

    season: str
    name: str
    role: str
    role_label: str
    team_id: str
    team_code: str
    played_matches: int | None
    grade_avg: float | None
    fanta_avg: float | None
    goals: int | None
    goals_against: int | None
    penalties_scored: int | None
    penalties_total: int | None
    penalties_saved: int | None
    assists: int | None
    yellow_cards: int | None
    red_cards: int | None
    player_url: str


def parse_statistiche_html(html: str) -> list[PlayerStatsRow]:
    """Estrae le righe di statistiche dalla pagina HTML scaricata.

    Args:
        html: HTML completo della pagina /statistiche-serie-a.

    Returns:
        Lista di `PlayerStatsRow`, una per ogni giocatore del listone.
    """
    soup = BeautifulSoup(html, "html.parser")
    season = _parse_season(soup)
    rows: list[PlayerStatsRow] = []
    for tr in soup.select(_PLAYER_ROW_SELECTOR):
        role_span = tr.select_one(_ROLE_SPAN_SELECTOR)
        player_link = tr.select_one("th.player-name a")
        penalties_scored, penalties_total = _parse_pair(_cell_text(tr, _key_cell("rig")))
        rows.append(
            PlayerStatsRow(
                season=season,
                name=tr.get("data-filter-keywords", "").strip(),
                role=(role_span.get("data-value") if role_span else "").strip(),
                role_label=(role_span.get("title") if role_span else "").strip(),
                team_id=tr.get("data-filter-team-id", "").strip(),
                team_code=_cell_text(tr, _key_cell("sq")),
                played_matches=_int_cell(tr, "pg"),
                grade_avg=_decimal_cell(tr, "mv"),
                fanta_avg=_decimal_cell(tr, "mfv"),
                goals=_int_cell(tr, "gol"),
                goals_against=_int_cell(tr, "gs"),
                penalties_scored=penalties_scored,
                penalties_total=penalties_total,
                penalties_saved=_int_cell(tr, "rp"),
                assists=_int_cell(tr, "ass"),
                yellow_cards=_int_cell(tr, "amm"),
                red_cards=_int_cell(tr, "esp"),
                player_url=(player_link.get("href") if player_link else "").strip(),
            )
        )
    return rows


def rows_to_csv(rows: list[PlayerStatsRow], path: Path) -> None:
    """Scrive le righe su CSV (utf-8-sig, leggibile da Excel).

    Args:
        rows: righe da serializzare.
        path: percorso di destinazione (la dir padre deve esistere).
    """
    write_csv((row.__dict__ for row in rows), path, CSV_COLUMNS)


def read_statistiche_csv(path: Path) -> list[PlayerStatsRow]:
    """Rilegge il CSV di cache come lista di `PlayerStatsRow`.

    Args:
        path: percorso del CSV prodotto da `rows_to_csv`.

    Returns:
        Le righe presenti nel file.
    """
    rows: list[PlayerStatsRow] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                PlayerStatsRow(
                    season=raw["season"],
                    name=raw["name"],
                    role=raw["role"],
                    role_label=raw["role_label"],
                    team_id=raw["team_id"],
                    team_code=raw["team_code"],
                    played_matches=to_int(raw["played_matches"]),
                    grade_avg=to_decimal(raw["grade_avg"]),
                    fanta_avg=to_decimal(raw["fanta_avg"]),
                    goals=to_int(raw["goals"]),
                    goals_against=to_int(raw["goals_against"]),
                    penalties_scored=to_int(raw["penalties_scored"]),
                    penalties_total=to_int(raw["penalties_total"]),
                    penalties_saved=to_int(raw["penalties_saved"]),
                    assists=to_int(raw["assists"]),
                    yellow_cards=to_int(raw["yellow_cards"]),
                    red_cards=to_int(raw["red_cards"]),
                    player_url=raw["player_url"],
                )
            )
    return rows


def read_season_stats(cache_dir: Path | None = None) -> dict[str, SeasonStats]:
    """Mappa la cache statistiche sulle entità condivise di logic.

    Args:
        cache_dir: directory della cache (default `CACHE_DIR`).

    Returns:
        Stats stagionali chiavate sull'URL della pagina giocatore (la chiave
        di join con `Player.url`). Vuote se la cache non esiste ancora.
    """
    path = (cache_dir or CACHE_DIR) / CACHE_FILE.name
    if not path.is_file():
        logger.warning("Cache statistiche assente: %s (esegui 'Aggiorna dati')", path)
        return {}
    rows = read_statistiche_csv(path)
    return {
        row.player_url: SeasonStats(
            played_matches=row.played_matches,
            grade_avg=row.grade_avg,
            fanta_avg=row.fanta_avg,
            goals=row.goals,
            goals_against=row.goals_against,
            penalties_scored=row.penalties_scored,
            penalties_total=row.penalties_total,
            penalties_saved=row.penalties_saved,
            assists=row.assists,
            yellow_cards=row.yellow_cards,
            red_cards=row.red_cards,
        )
        for row in rows
    }


def get_statistiche(
    force_refresh: bool = False,
    cache_dir: Path | None = None,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Unica porta d'accesso alle statistiche: cache-first, fetch on demand.

    Se la cache è fresca (meno di `CACHE_MAX_AGE_DAYS` giorni) la riusa;
    altrimenti scarica la pagina, la parsa, aggiorna il CSV e ritorna il
    DataFrame risultante.

    Args:
        force_refresh: ignora la cache e rifetica (pulsante "Aggiorna dati").
        cache_dir: directory della cache (per i test, `tmp_path`).
        session: sessione requests riutilizzabile (per i test).

    Returns:
        DataFrame con le colonne di `CSV_COLUMNS`.
    """
    cache_file = (cache_dir or CACHE_DIR) / CACHE_FILE.name
    if not force_refresh and is_cache_fresh(cache_file, CACHE_MAX_AGE_DAYS):
        logger.debug("Cache statistiche fresca: riuso di %s", cache_file)
        return read_cache_frame(cache_file)
    html = fetch_html(STATISTICHE_URL, session)
    rows = parse_statistiche_html(html)
    rows_to_csv(rows, cache_file)
    logger.info("Statistiche aggiornate: %d giocatori in %s", len(rows), cache_file)
    return read_cache_frame(cache_file)


def _key_cell(key: str) -> str:
    """Selettore della cella di colonna per data-col-key."""
    return f'td[data-col-key="{key}"]'


def _int_cell(tr: Tag, key: str) -> int | None:
    """Valore intero di una colonna (None se vuoto)."""
    return to_int(_cell_text(tr, _key_cell(key)))


def _decimal_cell(tr: Tag, key: str) -> float | None:
    """Valore decimale di una colonna (virgola italiana, None se vuoto)."""
    return to_decimal(_cell_text(tr, _key_cell(key)))


def _parse_pair(raw: str) -> tuple[int | None, int | None]:
    """Coppia "x / y" (rigori segnati/totali) → due int, tollerando vuoti."""
    parts = raw.split("/")
    if len(parts) != 2:
        return None, None
    return to_int(parts[0]), to_int(parts[1])


def _parse_season(soup: BeautifulSoup) -> str:
    """Stagione attiva (es. "2026/27") dal selettore stagione della pagina."""
    option = soup.select_one(_SEASON_SELECTOR)
    if option is None:
        return ""
    return option.get("value", "").strip()


def _cell_text(tr: Tag, selector: str) -> str:
    """Testo di una cella della riga, senza spazi superfluo."""
    cell = tr.select_one(selector)
    return cell.get_text(strip=True) if cell else ""
