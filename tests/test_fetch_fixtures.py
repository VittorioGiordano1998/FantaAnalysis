"""Test del parsing del calendario contro la fixture registrata.

Nessun test tocca la rete: `tests/fixtures/calendario_2026_27_week1.html` è
una slice reale della pagina `/serie-a/calendario` (giornata 1, stagione
2026/27) — la pagina rende ogni partita due volte, il parsing deve
deduplicare.
"""

from pathlib import Path

import pytest

from fetch_fixtures import (
    CACHE_FILE,
    FixtureRow,
    get_calendario,
    parse_calendar_html,
    read_calendario_csv,
    read_league_context,
    rows_to_csv,
)

FIXTURE = Path(__file__).parent / "fixtures" / "calendario_2026_27_week1.html"


def _fixture_rows() -> list[FixtureRow]:
    return parse_calendar_html(FIXTURE.read_text(encoding="utf-8"))


def test_parses_ten_unique_matches():
    rows = _fixture_rows()
    assert len(rows) == 10


def test_known_match_fields():
    rows = _fixture_rows()
    inter_monza = next(row for row in rows if row.home_team == "Inter" and row.away_team == "Monza")
    assert inter_monza.matchweek == 1
    assert inter_monza.home_id == "9"
    assert inter_monza.away_id == "143"
    assert inter_monza.date == "2026-08-22"
    assert inter_monza.time == "18:30"
    assert inter_monza.stadium == "Giuseppe Meazza"
    assert inter_monza.home_score == 0
    assert inter_monza.away_score == 0
    assert inter_monza.status == 0
    assert inter_monza.season == "2026-27"
    assert "/inter-monza/" in inter_monza.match_url


def test_all_teams_covered():
    rows = _fixture_rows()
    teams = {row.home_team for row in rows} | {row.away_team for row in rows}
    assert len(teams) == 20


def test_csv_round_trip(tmp_path):
    rows = _fixture_rows()
    path = tmp_path / CACHE_FILE.name
    rows_to_csv(rows, path)
    assert read_calendario_csv(path) == rows


def test_get_calendario_reuses_fresh_cache(tmp_path):
    rows = _fixture_rows()
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    frame = get_calendario(force_refresh=False, cache_dir=tmp_path)
    assert len(frame) == len(rows)
    assert frame.iloc[0]["matchweek"] == rows[0].matchweek


def test_read_league_context_missing_cache_returns_empty(tmp_path):
    context = read_league_context(cache_dir=tmp_path)
    assert context.season == ""
    assert context.current_matchweek == 1
    assert context.teams == {}
    assert context.league_gf_per_match is None


def test_read_league_context_neutral_before_season_start(tmp_path):
    rows = _synthetic_season(played_weeks=0)
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    context = read_league_context(cache_dir=tmp_path)
    assert context.season == "2026-27"
    assert context.current_matchweek == 1
    assert context.league_gf_per_match is None
    assert context.league_ga_per_match is None
    team_a = context.teams["A"]
    assert team_a.team_name == "Team A"
    assert team_a.gf_per_match is None
    assert team_a.ga_per_match is None
    assert team_a.upcoming_opponents == ("B",) * 5


def test_read_league_context_with_played_results(tmp_path):
    rows = _synthetic_season(played_weeks=2)
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    context = read_league_context(cache_dir=tmp_path)
    assert context.current_matchweek == 3
    assert context.league_gf_per_match == pytest.approx(1.25)
    assert context.league_ga_per_match == pytest.approx(1.25)
    team_a = context.teams["A"]
    assert team_a.gf_per_match == pytest.approx(2.0)
    assert team_a.ga_per_match == pytest.approx(1.0)
    assert team_a.upcoming_opponents == ("B",) * 5


def _synthetic_season(*, played_weeks: int) -> list[FixtureRow]:
    """Mini-stagione A-B/C-D su 8 settimane (prime `played_weeks` giocate)."""
    rows: list[FixtureRow] = []
    for week in range(1, 9):
        rows.append(_match(week, "A", "B", 2, 1, played=week <= played_weeks))
        rows.append(_match(week, "C", "D", 1, 1, played=week <= played_weeks))
    return rows


def _match(
    week: int,
    home: str,
    away: str,
    home_score: int,
    away_score: int,
    *,
    played: bool,
) -> FixtureRow:
    return FixtureRow(
        season="2026-27",
        matchweek=week,
        home_team=f"Team {home}",
        away_team=f"Team {away}",
        home_id=home,
        away_id=away,
        home_score=home_score,
        away_score=away_score,
        status=4 if played else 0,
        date=f"2026-08-{week:02d}",
        time="18:30",
        stadium="Stadio",
        match_url=f"/serie-a/calendario/{week}/2026-27/{home.lower()}-{away.lower()}/{100 + week}",
    )
