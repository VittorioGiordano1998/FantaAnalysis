"""Test del parsing delle statistiche contro le fixture registrate.

Nessun test tocca la rete: le fixture in `tests/fixtures/` sono slice reali
della pagina `/statistiche-serie-a` (stagioni 2026/27 e 2025/26).
"""

from pathlib import Path

from fetch_stats import (
    CACHE_FILE,
    PlayerStatsRow,
    get_statistiche,
    parse_statistiche_html,
    read_season_stats,
    read_statistiche_csv,
    rows_to_csv,
)

FIXTURE_CURRENT = Path(__file__).parent / "fixtures" / "statistiche_2026_27.html"
FIXTURE_PAST = Path(__file__).parent / "fixtures" / "statistiche_2025_26.html"


def _parse_fixture(path: Path) -> list[PlayerStatsRow]:
    return parse_statistiche_html(path.read_text(encoding="utf-8"))


def test_parses_all_rows_in_fixture():
    assert len(_parse_fixture(FIXTURE_CURRENT)) == 25
    assert len(_parse_fixture(FIXTURE_PAST)) == 25


def test_current_season_values_are_zero():
    rows = _parse_fixture(FIXTURE_CURRENT)
    assert {row.season for row in rows} == {"2026/27"}
    assert all(row.played_matches == 0 for row in rows)
    assert all(row.goals == 0 for row in rows)


def test_past_season_known_player_values():
    rows = _parse_fixture(FIXTURE_PAST)
    assert {row.season for row in rows} == {"2025/26"}
    de_luca = next(row for row in rows if row.name == "De Luca")
    assert de_luca.role == "pc"
    assert de_luca.team_code == "CRE"
    assert de_luca.played_matches == 1
    assert de_luca.grade_avg == 7.0
    assert de_luca.fanta_avg == 10.0
    assert de_luca.goals == 1
    assert de_luca.penalties_scored == 1
    assert de_luca.penalties_total == 1
    assert "/cremonese/de-luca/" in de_luca.player_url


def test_all_mantra_roles_parsed():
    rows = _parse_fixture(FIXTURE_CURRENT)
    roles = {row.role for row in rows}
    assert roles <= {"por", "dc", "b", "dd", "ds", "e", "m", "c", "w", "t", "a", "pc"}
    assert "por" in roles


def test_decimal_columns_parse_comma_values():
    rows = _parse_fixture(FIXTURE_PAST)
    with_values = [row for row in rows if row.grade_avg is not None]
    assert with_values
    assert all(isinstance(row.grade_avg, float) for row in with_values)


def test_csv_round_trip(tmp_path):
    rows = _parse_fixture(FIXTURE_PAST)
    path = tmp_path / CACHE_FILE.name
    rows_to_csv(rows, path)
    assert read_statistiche_csv(path) == rows


def test_get_statistiche_reuses_fresh_cache(tmp_path):
    rows = _parse_fixture(FIXTURE_PAST)
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    frame = get_statistiche(force_refresh=False, cache_dir=tmp_path)
    assert len(frame) == len(rows)
    assert frame.iloc[0]["name"] == rows[0].name


def test_read_season_stats_keyed_by_player_url(tmp_path):
    rows = _parse_fixture(FIXTURE_PAST)
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    stats_by_url = read_season_stats(cache_dir=tmp_path)
    assert len(stats_by_url) == len(rows)
    de_luca = next(row for row in rows if row.name == "De Luca")
    stats = stats_by_url[de_luca.player_url]
    assert stats.played_matches == 1
    assert stats.grade_avg == 7.0
    assert stats.goals == 1
    assert stats.penalties_scored == 1


def test_read_season_stats_missing_cache_returns_empty(tmp_path):
    assert read_season_stats(cache_dir=tmp_path) == {}
