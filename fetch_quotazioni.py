"""Scraping delle quotazioni da Fantacalcio.it con cache CSV settimanale.

Modulo del layer `data`: tutto l'I/O di rete e file vive qui. Il parsing e'
esposto come funzione pura (`parse_quotazioni_html`) testabile contro
fixture registrate; i test non toccano mai la rete.

La pagina di quotazioni rende la tabella server-side (la paginazione e'
client-side, tutti i giocatori sono nel DOM); basta un solo GET.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from entities import Player, Quote, Role
from fetch_common import (
    fetch_html,
    is_cache_fresh,
    read_cache_frame,
    to_int,
    write_csv,
)

logger = logging.getLogger(__name__)

QUOTAZIONI_URL = "https://www.fantacalcio.it/quotazioni-fantacalcio"

CACHE_DIR = Path("data")
CACHE_FILE = CACHE_DIR / "quotazioni.csv"
CACHE_MAX_AGE_DAYS = 7

CSV_COLUMNS = (
    "season",
    "name",
    "team_id",
    "team_code",
    "team_name",
    "role",
    "role_label",
    "qi",
    "qa",
    "fvm",
    "player_url",
)

_PLAYER_ROW_SELECTOR = "#prices tbody tr.player-row"
_ROLE_SPAN_SELECTOR = "span.role-mantra"
_TEAM_SELECTOR = "select#team"
_SEASON_SELECTOR = "select#season option[selected]"


@dataclass(frozen=True)
class QuotazioniRow:
    """Una riga del listone quotazioni (stagione, giocatore, ruolo Mantra)."""

    season: str
    name: str
    team_id: str
    team_code: str
    team_name: str
    role: str
    role_label: str
    qi: int | None
    qa: int | None
    fvm: int | None
    player_url: str


def parse_quotazioni_html(html: str) -> list[QuotazioniRow]:
    """Estrae le righe di quotazioni dalla pagina HTML scaricata.

    Args:
        html: HTML completo della pagina /quotazioni-fantacalcio.

    Returns:
        Lista di `QuotazioniRow`, una per ogni giocatore del listone.
    """
    soup = BeautifulSoup(html, "html.parser")
    team_names = _parse_team_names(soup)
    season = _parse_season(soup)
    rows: list[QuotazioniRow] = []
    for tr in soup.select(_PLAYER_ROW_SELECTOR):
        team_id = tr.get("data-filter-team-id", "").strip()
        role_span = tr.select_one(_ROLE_SPAN_SELECTOR)
        player_link = tr.select_one("th.player-name a")
        rows.append(
            QuotazioniRow(
                season=season,
                name=tr.get("data-filter-keywords", "").strip(),
                team_id=team_id,
                team_code=_cell_text(tr, "td.player-team"),
                team_name=team_names.get(team_id, ""),
                role=(role_span.get("data-value") if role_span else "").strip(),
                role_label=(role_span.get("title") if role_span else "").strip(),
                qi=to_int(_cell_text(tr, "td.player-mantra-initial-price")),
                qa=to_int(_cell_text(tr, "td.player-mantra-current-price")),
                fvm=to_int(_cell_text(tr, "td.player-mantra-fvm")),
                player_url=(player_link.get("href") if player_link else "").strip(),
            )
        )
    return rows


def rows_to_csv(rows: list[QuotazioniRow], path: Path) -> None:
    """Scrive le righe su CSV (utf-8-sig, leggibile da Excel).

    Args:
        rows: righe da serializzare.
        path: percorso di destinazione (la dir padre deve esistere).
    """
    write_csv((row.__dict__ for row in rows), path, CSV_COLUMNS)


def read_quotazioni_csv(path: Path) -> list[QuotazioniRow]:
    """Rilegge il CSV di cache come lista di `QuotazioniRow`.

    Args:
        path: percorso del CSV prodotto da `rows_to_csv`.

    Returns:
        Le righe presenti nel file.
    """
    rows: list[QuotazioniRow] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                QuotazioniRow(
                    season=raw["season"],
                    name=raw["name"],
                    team_id=raw["team_id"],
                    team_code=raw["team_code"],
                    team_name=raw["team_name"],
                    role=raw["role"],
                    role_label=raw["role_label"],
                    qi=to_int(raw["qi"]),
                    qa=to_int(raw["qa"]),
                    fvm=to_int(raw["fvm"]),
                    player_url=raw["player_url"],
                )
            )
    return rows


def read_players(cache_dir: Path | None = None) -> list[Player]:
    """Mappa la cache quotazioni sulle entità condivise di logic.

    Args:
        cache_dir: directory della cache (default `CACHE_DIR`).

    Returns:
        Lista di `Player` con quotazione ma senza stats (vedi
        `fetch_stats.read_season_stats` + `entities.attach_stats`).
        Vuota se la cache non esiste ancora (primo avvio su Cloud).
    """
    path = (cache_dir or CACHE_DIR) / CACHE_FILE.name
    if not path.is_file():
        logger.warning("Cache quotazioni assente: %s (esegui 'Aggiorna dati')", path)
        return []
    rows = read_quotazioni_csv(path)
    return [
        Player(
            name=row.name,
            role=Role(row.role),
            team_id=row.team_id,
            team_code=row.team_code,
            team_name=row.team_name,
            quote=Quote(qi=row.qi, qa=row.qa, fvm=row.fvm),
            url=row.player_url,
        )
        for row in rows
    ]


def get_quotazioni(
    force_refresh: bool = False,
    cache_dir: Path | None = None,
    session: requests.Session | None = None,
) -> pd.DataFrame:
    """Unica porta d'accesso alle quotazioni: cache-first, fetch on demand.

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
        logger.debug("Cache quotazioni fresca: riuso di %s", cache_file)
        return read_cache_frame(cache_file)
    html = fetch_html(QUOTAZIONI_URL, session)
    rows = parse_quotazioni_html(html)
    rows_to_csv(rows, cache_file)
    logger.info("Quotazioni aggiornate: %d giocatori in %s", len(rows), cache_file)
    return read_cache_frame(cache_file)


def cache_mtime(cache_file: Path | None = None) -> datetime | None:
    """Timestamp dell'ultimo aggiornamento della cache, se presente.

    Args:
        cache_file: percorso della cache (default `CACHE_FILE`).

    Returns:
        Il mtime del file oppure `None` se la cache non esiste ancora.
    """
    cache_file = cache_file or CACHE_FILE
    if not cache_file.is_file():
        return None
    return datetime.fromtimestamp(cache_file.stat().st_mtime)


def _parse_team_names(soup: BeautifulSoup) -> dict[str, str]:
    """Mappa id squadra → nome dal filtro `select#team` della pagina."""
    select = soup.select_one(_TEAM_SELECTOR)
    if select is None:
        return {}
    return {
        option.get("value"): option.get_text(strip=True)
        for option in select.find_all("option")
        if option.get("value")
    }


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
