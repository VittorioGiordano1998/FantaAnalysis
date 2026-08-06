"""Test del parsing delle quotazioni contro la fixture registrata.

Nessun test tocca la rete: la fixture `tests/fixtures/quotazioni_2026_27.html`
è una slice reale della pagina Fantacalcio.it (stagione 2026/27).
"""

from pathlib import Path

from entities import Role
from fetch_quotazioni import (
    CACHE_FILE,
    QuotazioniRow,
    get_quotazioni,
    parse_quotazioni_html,
    read_players,
    read_quotazioni_csv,
    rows_to_csv,
)

FIXTURE = Path(__file__).parent / "fixtures" / "quotazioni_2026_27.html"


def _fixture_rows() -> list[QuotazioniRow]:
    return parse_quotazioni_html(FIXTURE.read_text(encoding="utf-8"))


def test_parses_all_players_in_fixture():
    rows = _fixture_rows()
    assert len(rows) == 494


def test_known_player_fields():
    rows = _fixture_rows()
    martinez = next(row for row in rows if row.name == "Martinez L.")
    assert martinez.role == "pc"
    assert martinez.role_label == "Punta centrale"
    assert martinez.team_code == "INT"
    assert martinez.team_name == "Inter"
    assert martinez.qi == 35
    assert martinez.qa == 35
    assert martinez.fvm == 370
    assert "/inter/martinez-l/" in martinez.player_url


def test_season_is_current():
    rows = _fixture_rows()
    assert {row.season for row in rows} == {"2026/27"}


def test_roles_cover_all_mantra_codes():
    rows = _fixture_rows()
    roles = {row.role for row in rows}
    assert roles == {"por", "dc", "b", "dd", "ds", "e", "m", "c", "w", "t", "a", "pc"}


def test_team_names_resolved():
    rows = _fixture_rows()
    team_names = {row.team_name for row in rows}
    assert len(team_names) == 20
    assert "Atalanta" in team_names
    assert "Venezia" in team_names


def test_no_empty_names():
    rows = _fixture_rows()
    assert all(row.name for row in rows)
    assert all(row.team_code for row in rows)
    assert all(row.team_name for row in rows)


def test_csv_round_trip(tmp_path):
    rows = _fixture_rows()
    path = tmp_path / CACHE_FILE.name
    rows_to_csv(rows, path)
    assert read_quotazioni_csv(path) == rows


def test_get_quotazioni_reuses_fresh_cache(tmp_path):
    rows = _fixture_rows()
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    frame = get_quotazioni(force_refresh=False, cache_dir=tmp_path)
    assert len(frame) == len(rows)
    assert frame.iloc[0]["name"] == rows[0].name
    assert frame["qi"].dtype == "int64"


def test_read_players_maps_entities(tmp_path):
    rows = _fixture_rows()[:3]
    rows_to_csv(rows, tmp_path / CACHE_FILE.name)
    players = read_players(cache_dir=tmp_path)
    assert len(players) == 3
    martinez = players[0]
    assert martinez.name == "Martinez L."
    assert martinez.role == Role.PC
    assert martinez.team_id == "9"
    assert martinez.team_code == "INT"
    assert martinez.team_name == "Inter"
    assert martinez.quote.qi == 35
    assert martinez.quote.fvm == 370
    assert martinez.stats is None


def test_read_players_missing_cache_returns_empty(tmp_path):
    assert read_players(cache_dir=tmp_path) == []
