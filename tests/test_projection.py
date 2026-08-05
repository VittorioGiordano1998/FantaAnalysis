"""Test unitari del modello di proiezione (ADR-0002).

Formule pure testate con fixture in-memory: nessun I/O, nessuna rete.
"""

import pytest

from entities import ROLE_GROUP, Player, Quote, Role, RoleGroup, SeasonStats, attach_stats
from projection import (
    LeagueContext,
    PlayerProjection,
    TeamContext,
    calendar_multiplier,
    expected_remaining_matches,
    playing_share,
    points_per_match,
    project,
)

PLAYER_URL = "https://www.fantacalcio.it/serie-a/squadre/inter/x/1"


def _player(
    role: Role = Role.PC,
    fvm: int = 300,
    stats: SeasonStats | None = None,
    team_id: str = "9",
    url: str = PLAYER_URL,
) -> Player:
    return Player(
        name="X",
        role=role,
        team_id=team_id,
        team_code="INT",
        team_name="Inter",
        quote=Quote(qi=30, qa=30, fvm=fvm),
        url=url,
        stats=stats,
    )


def _context(
    *,
    current_matchweek: int = 1,
    league_gf: float | None = None,
    league_ga: float | None = None,
    teams: dict[str, TeamContext] | None = None,
) -> LeagueContext:
    return LeagueContext(
        season="2026-27",
        current_matchweek=current_matchweek,
        teams=teams or {},
        league_gf_per_match=league_gf,
        league_ga_per_match=league_ga,
    )


def test_points_per_match_fvm_fallback_without_stats():
    assert points_per_match(_player(fvm=300)) == 3.0
    assert points_per_match(_player(fvm=0)) == 0.0


def test_points_per_match_fanta_avg_after_min_matches():
    stats = SeasonStats(played_matches=10, fanta_avg=7.5)
    assert points_per_match(_player(stats=stats)) == 7.5


def test_points_per_match_blend_below_min_matches():
    stats = SeasonStats(played_matches=1, fanta_avg=6.0)
    assert points_per_match(_player(fvm=200, stats=stats)) == 4.0


def test_points_per_match_zero_played_uses_fvm():
    stats = SeasonStats(played_matches=0, fanta_avg=8.0)
    assert points_per_match(_player(fvm=200, stats=stats)) == 2.0


def test_playing_share_neutral_at_season_start():
    league = _context(current_matchweek=1)
    assert playing_share(_player(stats=SeasonStats(played_matches=0)), league) == 1.0
    assert playing_share(_player(), league) == 1.0


def test_playing_share_from_played_rounds():
    league = _context(current_matchweek=11)
    stats = SeasonStats(played_matches=8)
    assert playing_share(_player(stats=stats), league) == 0.8


def test_playing_share_capped_at_one():
    league = _context(current_matchweek=11)
    stats = SeasonStats(played_matches=12)
    assert playing_share(_player(stats=stats), league) == 1.0


def test_expected_remaining_matches():
    league = _context(current_matchweek=1)
    assert expected_remaining_matches(_player(), league) == 38
    league = _context(current_matchweek=11)
    stats = SeasonStats(played_matches=8)
    assert expected_remaining_matches(_player(stats=stats), league) == pytest.approx(22.4)


def test_calendar_multiplier_neutral_without_results():
    league = _context(teams={"9": _team_context()})
    assert calendar_multiplier(_player(), league) == 1.0


def test_calendar_multiplier_neutral_without_opponent_data():
    teams = {"9": _team_context(upcoming=("13", "10"))}
    league = _context(teams=teams, league_gf=1.2, league_ga=1.2)
    assert calendar_multiplier(_player(), league) == 1.0


def test_attacker_multiplier_with_weak_defense_is_capped():
    teams = {
        "9": _team_context(upcoming=("13", "10", "11", "12", "14")),
        "13": _team_context(ga=2.5),
        "10": _team_context(ga=2.5),
        "11": _team_context(ga=2.5),
        "12": _team_context(ga=2.5),
        "14": _team_context(ga=2.5),
    }
    league = _context(teams=teams, league_gf=1.0, league_ga=1.0)
    assert calendar_multiplier(_player(), league) == pytest.approx(1.1)


def test_attacker_multiplier_with_strong_defense_is_capped_low():
    teams = {
        "9": _team_context(upcoming=("13",)),
        "13": _team_context(ga=0.5),
    }
    league = _context(teams=teams, league_gf=1.0, league_ga=1.0)
    assert calendar_multiplier(_player(), league) == pytest.approx(0.9)


def test_defender_multiplier_inverted_on_opponent_attack():
    teams = {
        "9": _team_context(upcoming=("13",)),
        "13": _team_context(gf=0.5),
    }
    league = _context(teams=teams, league_gf=1.0, league_ga=1.0)
    assert calendar_multiplier(_player(role=Role.DC), league) == pytest.approx(1.1)


def test_defender_penalized_by_strong_opponent_attack():
    teams = {
        "9": _team_context(upcoming=("13",)),
        "13": _team_context(gf=2.5),
    }
    league = _context(teams=teams, league_gf=1.0, league_ga=1.0)
    assert calendar_multiplier(_player(role=Role.POR), league) == pytest.approx(0.9)


def test_project_total_with_calendar_on_five_weeks_only():
    teams = {
        "9": _team_context(upcoming=("13",) * 5),
        "13": _team_context(ga=2.5),
    }
    league = _context(teams=teams, league_gf=1.0, league_ga=1.0)
    result = project(_player(fvm=200, stats=SeasonStats(played_matches=10, fanta_avg=2.0)), league)
    assert isinstance(result, PlayerProjection)
    assert result.points_per_match == 2.0
    assert result.matches_expected == 38
    assert result.calendar_multiplier == pytest.approx(1.1)
    assert result.total_points == pytest.approx(2.0 * (1.1 * 5 + 33))


def test_project_total_neutral_calendar():
    league = _context()
    result = project(_player(fvm=200, stats=SeasonStats(played_matches=10, fanta_avg=2.0)), league)
    assert result.total_points == pytest.approx(76.0)


def test_role_group_mapping():
    assert ROLE_GROUP[Role.POR] == RoleGroup.P
    assert ROLE_GROUP[Role.DC] == RoleGroup.D
    assert ROLE_GROUP[Role.B] == RoleGroup.D
    assert ROLE_GROUP[Role.E] == RoleGroup.C
    assert ROLE_GROUP[Role.W] == RoleGroup.C
    assert ROLE_GROUP[Role.T] == RoleGroup.C
    assert ROLE_GROUP[Role.A] == RoleGroup.A
    assert ROLE_GROUP[Role.PC] == RoleGroup.A


def test_attach_stats_merges_by_url():
    players = [_player(url=PLAYER_URL), _player(url="other")]
    stats = SeasonStats(played_matches=5, goals=3)
    merged = attach_stats(players, {PLAYER_URL: stats})
    assert merged[0].stats == stats
    assert merged[1].stats is None


def _team_context(
    *,
    gf: float | None = None,
    ga: float | None = None,
    upcoming: tuple[str, ...] = (),
) -> TeamContext:
    return TeamContext(
        team_id="9",
        team_name="Inter",
        gf_per_match=gf,
        ga_per_match=ga,
        upcoming_opponents=upcoming,
    )
