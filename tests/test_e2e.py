"""Test end-to-end dell'asta simulata con dati reali (M7).

Usa le fixture registrate in `tests/fixtures/` (listone 2026/27 completo,
stats 2026/27 a inizio stagione, calendario settimana 1): nessuna rete,
nessun filesystem reale (tmp_path). Simula l'asta dalla prima presa alla
rosa finale attraversando stato → proiezione → ottimizzazione → limite di
spesa → export/import.
"""

from collections import Counter
from pathlib import Path

import pytest

from entities import ROLE_GROUP, RoleGroup, TakenPick, attach_stats
from fetch_fixtures import (
    CACHE_FILE as CAL_CACHE_FILE,
)
from fetch_fixtures import (
    parse_calendar_html,
    read_league_context,
)
from fetch_fixtures import (
    rows_to_csv as calendar_to_csv,
)
from fetch_quotazioni import (
    CACHE_FILE as QUOT_CACHE_FILE,
)
from fetch_quotazioni import (
    parse_quotazioni_html,
    read_players,
)
from fetch_quotazioni import (
    rows_to_csv as quotazioni_to_csv,
)
from fetch_stats import (
    CACHE_FILE as STATS_CACHE_FILE,
)
from fetch_stats import (
    parse_statistiche_html,
    read_season_stats,
)
from fetch_stats import (
    rows_to_csv as stats_to_csv,
)
from optimize import optimize_squad, spending_limit
from projection import LeagueContext
from state import (
    add_taken,
    default_state,
    export_state,
    import_state,
    slots_remaining,
    spent_budget,
    taken_urls,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
QUOTAZIONI_HTML = FIXTURE_DIR / "quotazioni_2026_27.html"
STATS_HTML = FIXTURE_DIR / "statistiche_2026_27.html"
CALENDAR_HTML = FIXTURE_DIR / "calendario_2026_27_week1.html"


def _real_pool(tmp_path):
    """Pool reale 2026/27: 494 giocatori, stats di inizio stagione."""
    rows = parse_quotazioni_html(QUOTAZIONI_HTML.read_text(encoding="utf-8"))
    quotazioni_to_csv(rows, tmp_path / QUOT_CACHE_FILE.name)
    players = read_players(cache_dir=tmp_path)

    stats_rows = parse_statistiche_html(STATS_HTML.read_text(encoding="utf-8"))
    stats_to_csv(stats_rows, tmp_path / STATS_CACHE_FILE.name)
    stats_by_url = read_season_stats(cache_dir=tmp_path)
    players = attach_stats(players, stats_by_url)

    calendar_rows = parse_calendar_html(CALENDAR_HTML.read_text(encoding="utf-8"))
    calendar_to_csv(calendar_rows, tmp_path / CAL_CACHE_FILE.name)
    league = read_league_context(cache_dir=tmp_path)
    return players, league


def _group_counts(players) -> dict[RoleGroup, int]:
    return Counter(ROLE_GROUP[p.role] for p in players)


def test_asta_simulata_fino_alla_rosa_finale(tmp_path):
    players, league = _real_pool(tmp_path)
    assert isinstance(league, LeagueContext)
    assert len(players) == 494
    assert league.current_matchweek == 1

    state = default_state()

    # 1. rosa ottimale iniziale sul pool completo
    squad = optimize_squad(players, league, budget=state.budget)
    assert squad.status == "Optimal"
    assert len(squad.selected) == 25
    assert squad.total_cost <= state.budget
    assert _group_counts(squad.selected) == {
        RoleGroup.P: 2,
        RoleGroup.D: 8,
        RoleGroup.C: 8,
        RoleGroup.A: 7,
    }

    # 2. le altre squadre prendono i primi 3 della rosa → esclusi dagli ottimi
    for _ in range(3):
        top = squad.selected[0]
        state = add_taken(state, TakenPick(top.url, "Squadra B", None))
        squad = optimize_squad(players, league, budget=state.budget, taken_urls=taken_urls(state))
        assert squad.status == "Optimal"
        assert top.url not in {p.url for p in squad.selected}
        assert len(squad.selected) == 25

    # 3. limite di spesa su un giocatore rimasto (pool ancora ampio)
    remaining = [p for p in players if p.url not in taken_urls(state)]
    assert len(remaining) == 494 - 3
    target = max(remaining, key=lambda p: p.quote.qi or 0)
    limit = spending_limit(
        target,
        players,
        league,
        budget=state.budget,
        taken_urls=taken_urls(state),
    )
    assert limit.status == "Optimal"
    assert 0 <= limit.max_price <= state.budget

    # 4. prendo l'intera rosa ottimale corrente per la propria squadra (prezzo QI)
    for pick in squad.selected:
        state = add_taken(state, TakenPick(pick.url, state.own_team, pick.quote.qi or 0))
    assert spent_budget(state) <= state.budget
    assert spent_budget(state) == squad.total_cost
    assert slots_remaining(state, players) == {
        RoleGroup.P: 0,
        RoleGroup.D: 0,
        RoleGroup.C: 0,
        RoleGroup.A: 0,
    }

    # 5. una presa duplicata è rifiutata
    with pytest.raises(ValueError):
        add_taken(state, TakenPick(squad.selected[0].url, "Squadra B", None))

    # 6. lo stato completa il round-trip export/import
    assert import_state(export_state(state)) == state
