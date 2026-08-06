"""Scraping del calendario Serie A Fantacalcio.it con cache CSV settimanale.

Modulo del layer `data`: tutto l'I/O di rete e file vive qui. Il calendario
mostra una giornata per volta (`/serie-a/calendario/<N>`); `get_calendario`
scarica tutte le giornate (rate-limited) e le consolida in un solo CSV.

La pagina rende ogni partita due volte (lista per data + lista per giornata):
il parsing deduplica per URL match.
"""

from __future__ import annotations

import csv
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag

from fetch_common import (
    fetch_html,
    is_cache_fresh,
    read_cache_frame,
    to_int,
    write_csv,
)
from projection import NEXT_WEEKS, LeagueContext, TeamContext
from utility import CalendarWeek, TeamCalendar

logger = logging.getLogger(__name__)

CALENDAR_URL = "https://www.fantacalcio.it/serie-a/calendario"

CACHE_DIR = Path("data")
CACHE_FILE = CACHE_DIR / "calendario.csv"
CACHE_MAX_AGE_DAYS = 7

MATCHWEEKS = range(1, 39)

CSV_COLUMNS = (
    "season",
    "matchweek",
    "home_team",
    "away_team",
    "home_id",
    "away_id",
    "home_score",
    "away_score",
    "status",
    "date",
    "time",
    "stadium",
    "match_url",
)

_MATCH_PILL_SELECTOR = "div.match-pill"
_TEAM_NAME_SELECTOR = 'meta[itemprop="name"]'
_SEASON_PATTERN = re.compile(r"/calendario/\d+/(\d{4}-\d{2})/")
_WEEK_PATTERN = re.compile(r"/calendario/(\d+)/")


@dataclass(frozen=True)
class FixtureRow:
    """Una partita del calendario (casa, trasferta, risultato, stato)."""

    season: str
    matchweek: int
    home_team: str
    away_team: str
    home_id: str
    away_id: str
    home_score: int | None
    away_score: int | None
    status: int
    date: str
    time: str
    stadium: str
    match_url: str


def parse_calendar_html(html: str) -> list[FixtureRow]:
    """Estrae le partite dalla pagina calendario di una giornata.

    La pagina rende ogni partita due volte (per data e per giornata): le
    righe sono deduplicate per URL partita, tenendo la prima occorrenza.
    La giornata si ricava dall'URL partita (`/calendario/<N>/...`), più
    affidabile del valore nel DOM quando la pagina contiene più giornate.

    Args:
        html: HTML di `/serie-a/calendario/<N>` (o `/serie-a/calendario`).

    Returns:
        Lista di `FixtureRow`, una per partita della giornata.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows: list[FixtureRow] = []
    seen: set[str] = set()
    for pill in soup.select(_MATCH_PILL_SELECTOR):
        match_url = _pill_url(pill)
        if not match_url or match_url in seen:
            continue
        seen.add(match_url)
        home_label = pill.select_one("label.team-home")
        away_label = pill.select_one("label.team-away")
        rows.append(
            FixtureRow(
                season=_parse_season(match_url),
                matchweek=_parse_week(match_url) or to_int(_cell_text(pill, "div.matchweek")) or 0,
                home_team=_team_name(home_label),
                away_team=_team_name(away_label),
                home_id=_team_id(home_label),
                away_id=_team_id(away_label),
                home_score=to_int(_cell_text(pill, "span.score-home")),
                away_score=to_int(_cell_text(pill, "span.score-away")),
                status=to_int(pill.get("data-match-status")) or 0,
                date=_attr_text(pill, 'meta[itemprop="startDate"]', "content"),
                time=_cell_text(pill, "span.hours"),
                stadium=_cell_text(pill, "span.stadium"),
                match_url=match_url,
            )
        )
    return rows


def rows_to_csv(rows: list[FixtureRow], path: Path) -> None:
    """Scrive le righe su CSV (utf-8-sig, leggibile da Excel).

    Args:
        rows: righe da serializzare.
        path: percorso di destinazione (la dir padre deve esistere).
    """
    write_csv((row.__dict__ for row in rows), path, CSV_COLUMNS)


def read_calendario_csv(path: Path) -> list[FixtureRow]:
    """Rilegge il CSV di cache come lista di `FixtureRow`.

    Args:
        path: percorso del CSV prodotto da `rows_to_csv`.

    Returns:
        Le righe presenti nel file.
    """
    rows: list[FixtureRow] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            rows.append(
                FixtureRow(
                    season=raw["season"],
                    matchweek=to_int(raw["matchweek"]) or 0,
                    home_team=raw["home_team"],
                    away_team=raw["away_team"],
                    home_id=raw["home_id"],
                    away_id=raw["away_id"],
                    home_score=to_int(raw["home_score"]),
                    away_score=to_int(raw["away_score"]),
                    status=to_int(raw["status"]) or 0,
                    date=raw["date"],
                    time=raw["time"],
                    stadium=raw["stadium"],
                    match_url=raw["match_url"],
                )
            )
    return rows


def read_league_context(cache_dir: Path | None = None) -> LeagueContext:
    """Mappa la cache calendario sul contesto di proiezione (ADR-0002).

    La forza squadra deriva dai match già giocati (status ≠ 0); la giornata
    corrente è l'ultima giocata + 1 (1 se nessuna giocata); i prossimi 5
    avversari sono le partite future più vicine di ogni squadra.

    Args:
        cache_dir: directory della cache (default `CACHE_DIR`).

    Returns:
        Contesto campionato con forze squadra e calendario prossimo.
        Contesto vuoto se la cache non esiste ancora (primo avvio su Cloud).
    """
    path = (cache_dir or CACHE_DIR) / CACHE_FILE.name
    if not path.is_file():
        logger.warning("Cache calendario assente: %s (esegui 'Aggiorna dati')", path)
        return LeagueContext(season="", current_matchweek=1, teams={})
    frame = read_cache_frame(path)
    if frame.empty:
        return LeagueContext(season="", current_matchweek=1, teams={})
    season = str(frame["season"].iloc[0])
    played = frame[frame["status"] != 0]
    current_matchweek = _current_matchweek(frame)
    teams = _team_contexts(frame, played, current_matchweek)
    league_gf, league_ga = _league_averages(played)
    return LeagueContext(
        season=season,
        current_matchweek=current_matchweek,
        teams=teams,
        league_gf_per_match=league_gf,
        league_ga_per_match=league_ga,
    )


def read_remaining_calendar(
    cache_dir: Path | None = None,
) -> dict[str, TeamCalendar]:
    """Calendario rimanente per squadra: gli avversari delle giornate ancora da giocare.

    La giornata corrente è l'ultima giocata + 1 (1 se nessuna giocata);
    ogni squadra ha un avversario per giornata rimanente, ordinato per
    matchweek (stesso indice = stessa giornata per tutte le squadre).

    Args:
        cache_dir: directory della cache (default `CACHE_DIR`).

    Returns:
        team_id → `TeamCalendar` (vuoto se la cache non esiste ancora).
    """
    path = (cache_dir or CACHE_DIR) / CACHE_FILE.name
    if not path.is_file():
        logger.warning("Cache calendario assente: %s (esegui 'Aggiorna dati')", path)
        return {}
    frame = read_cache_frame(path)
    if frame.empty:
        return {}
    current_matchweek = _current_matchweek(frame)
    future = frame[frame["matchweek"].astype(int) >= current_matchweek]
    calendars: dict[str, TeamCalendar] = {}
    team_ids = sorted(set(future["home_id"].astype(str)) | set(future["away_id"].astype(str)))
    for team_id in team_ids:
        matches = future[
            (future["home_id"].astype(str) == team_id) | (future["away_id"].astype(str) == team_id)
        ].sort_values(["matchweek", "date"])
        weeks = tuple(
            CalendarWeek(
                matchweek=int(row["matchweek"]),
                opponent_id=str(row["away_id"])
                if str(row["home_id"]) == team_id
                else str(row["home_id"]),
            )
            for _, row in matches.iterrows()
        )
        calendars[team_id] = TeamCalendar(team_id=team_id, weeks=weeks)
    return calendars


def _current_matchweek(frame: pd.DataFrame) -> int:
    """Giornata corrente: ultima giocata + 1 (1 se nessuna giocata)."""
    played = frame[frame["status"] != 0]
    return int(played["matchweek"].max()) + 1 if not played.empty else 1


def _team_contexts(
    frame: pd.DataFrame,
    played: pd.DataFrame,
    current_matchweek: int,
) -> dict[str, TeamContext]:
    """Contesti squadra: forze dai match giocati, prossimi 5 avversari."""
    team_ids = sorted(set(frame["home_id"].astype(str)) | set(frame["away_id"].astype(str)))
    contexts: dict[str, TeamContext] = {}
    for team_id in team_ids:
        contexts[team_id] = TeamContext(
            team_id=team_id,
            team_name=_team_name_from_frame(frame, team_id),
            gf_per_match=_team_avg(frame, played, team_id, scored=True),
            ga_per_match=_team_avg(frame, played, team_id, scored=False),
            upcoming_opponents=_upcoming_opponents(frame, team_id, current_matchweek),
        )
    return contexts


def _team_avg(
    frame: pd.DataFrame,
    played: pd.DataFrame,
    team_id: str,
    *,
    scored: bool,
) -> float | None:
    """Media gol fatti/subiti a partita per la squadra (None se mai giocato)."""
    if played.empty:
        return None
    home = played[played["home_id"].astype(str) == team_id]
    away = played[played["away_id"].astype(str) == team_id]
    if scored:
        goals = list(home["home_score"]) + list(away["away_score"])
    else:
        goals = list(home["away_score"]) + list(away["home_score"])
    goals = [int(g) for g in goals if pd.notna(g)]
    if not goals:
        return None
    return float(sum(goals)) / len(goals)


def _upcoming_opponents(
    frame: pd.DataFrame,
    team_id: str,
    current_matchweek: int,
) -> tuple[str, ...]:
    """Prossimi 5 avversari (partite future ordinate per giornata/data)."""
    future = frame[
        (frame["matchweek"].astype(int) > current_matchweek)
        & ((frame["home_id"].astype(str) == team_id) | (frame["away_id"].astype(str) == team_id))
    ].sort_values(["matchweek", "date"])
    opponents: list[str] = []
    for _, row in future.iterrows():
        opponent = row["away_id"] if str(row["home_id"]) == team_id else row["home_id"]
        opponents.append(str(opponent))
        if len(opponents) >= NEXT_WEEKS:
            break
    return tuple(opponents)


def _league_averages(played: pd.DataFrame) -> tuple[float | None, float | None]:
    """Medie di lega gol a partita (None se nessun match giocato)."""
    if played.empty:
        return None, None
    home = [g for g in played["home_score"] if pd.notna(g)]
    away = [g for g in played["away_score"] if pd.notna(g)]
    if not home or not away:
        return None, None
    matches = len(home)
    per_match = (sum(home) + sum(away)) / (2 * matches)
    return per_match, per_match


def _team_name_from_frame(frame: pd.DataFrame, team_id: str) -> str:
    """Nome squadra dal primo match del calendario che la coinvolge."""
    home = frame.loc[frame["home_id"].astype(str) == team_id, "home_team"]
    if not home.empty:
        return str(home.iloc[0])
    away = frame.loc[frame["away_id"].astype(str) == team_id, "away_team"]
    return str(away.iloc[0]) if not away.empty else ""


def get_calendario(
    force_refresh: bool = False,
    cache_dir: Path | None = None,
    session: requests.Session | None = None,
    matchweeks: range = MATCHWEEKS,
) -> pd.DataFrame:
    """Unica porta d'accesso al calendario: cache-first, fetch on demand.

    Se la cache è fresca (meno di `CACHE_MAX_AGE_DAYS` giorni) la riusa;
    altrimenti scarica una pagina per giornata (rate-limited a
    `REQUEST_DELAY_SECONDS`), consolida le partite deduplicate e aggiorna il
    CSV.

    Args:
        force_refresh: ignora la cache e rifetica (pulsante "Aggiorna dati").
        cache_dir: directory della cache (per i test, `tmp_path`).
        session: sessione requests riutilizzabile (per i test).
        matchweeks: giornate da scaricare (default: 1..38).

    Returns:
        DataFrame con le colonne di `CSV_COLUMNS`.
    """
    cache_file = (cache_dir or CACHE_DIR) / CACHE_FILE.name
    if not force_refresh and is_cache_fresh(cache_file, CACHE_MAX_AGE_DAYS):
        logger.debug("Cache calendario fresca: riuso di %s", cache_file)
        return read_cache_frame(cache_file)
    rows: list[FixtureRow] = []
    seen: set[str] = set()
    for week in matchweeks:
        html = fetch_html(f"{CALENDAR_URL}/{week}", session)
        for row in parse_calendar_html(html):
            if row.match_url in seen:
                continue
            seen.add(row.match_url)
            rows.append(row)
    rows.sort(key=lambda row: (row.matchweek, row.date, row.home_team))
    rows_to_csv(rows, cache_file)
    logger.info("Calendario aggiornato: %d partite in %s", len(rows), cache_file)
    return read_cache_frame(cache_file)


def _pill_url(pill: Tag) -> str:
    """URL partita (dal link risultato), normalizzato al solo path.

    La pagina mescola href assoluti e relativi per la stessa partita: la
    normalizzazione al path rende confrontabili i duplicati per il dedup.
    """
    link = pill.select_one("a.match-score")
    if link is None:
        return ""
    return urlsplit(link.get("href", "").strip()).path


def _team_name(label: Tag | None) -> str:
    """Nome squadra dal meta schema.org del label casa/trasferta."""
    if label is None:
        return ""
    meta = label.select_one(_TEAM_NAME_SELECTOR)
    return meta.get("content", "").strip() if meta else ""


def _team_id(label: Tag | None) -> str:
    """Id squadra dall'attributo `for="team-N"` del label."""
    if label is None:
        return ""
    for_attr = label.get("for", "")
    return for_attr.removeprefix("team-")


def _parse_season(match_url: str) -> str:
    """Stagione (es. "2026-27") dall'URL partita."""
    match = _SEASON_PATTERN.search(match_url)
    return match.group(1) if match else ""


def _parse_week(match_url: str) -> int | None:
    """Giornata dall'URL partita (`/calendario/<N>/...`)."""
    match = _WEEK_PATTERN.search(match_url)
    return to_int(match.group(1)) if match else None


def _cell_text(scope: Tag, selector: str) -> str:
    """Testo di un elemento dentro `scope`, senza spazi superfluo."""
    cell = scope.select_one(selector)
    return cell.get_text(strip=True) if cell else ""


def _attr_text(scope: Tag, selector: str, attr: str) -> str:
    """Attributo di un elemento dentro `scope`."""
    element = scope.select_one(selector)
    return element.get(attr, "").strip() if element else ""
