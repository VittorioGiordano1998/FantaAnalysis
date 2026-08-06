"""Test del punteggio di utilità e del mapping modulo (layer logic).

Lega sintetica costruita a mano: niente rete, niente filesystem. Le
componenti slot/calendario/copertura si testano isolandole (le altre due
componenti sono neutre quando mancano i dati).
"""

import pytest

from entities import Player, Quote, Role, RoleGroup
from projection import LeagueContext, TeamContext
from utility import (
    MODULES,
    TeamCalendar,
    opponent_outlook,
    team_strengths_from_players,
    utility_score,
)

FULL_SLOTS = {
    RoleGroup.P: 2,
    RoleGroup.D: 8,
    RoleGroup.C: 8,
    RoleGroup.A: 7,
}


def _player(name: str, role: Role, team_id: str, url: str) -> Player:
    return Player(
        name=name,
        role=role,
        team_id=team_id,
        team_code="TC",
        team_name="Team",
        quote=Quote(qi=10, qa=10, fvm=100),
        url=url,
    )


def _team(
    team_id: str,
    name: str,
    gf: float | None,
    ga: float | None,
    opponents: tuple[str, ...],
) -> TeamContext:
    return TeamContext(
        team_id=team_id,
        team_name=name,
        gf_per_match=gf,
        ga_per_match=ga,
        upcoming_opponents=opponents,
    )


def _league(teams: list[TeamContext], gf: float = 1.0, ga: float = 1.0) -> LeagueContext:
    return LeagueContext(
        season="2026/27",
        current_matchweek=3,
        teams={team.team_id: team for team in teams},
        league_gf_per_match=gf,
        league_ga_per_match=ga,
    )


def test_module_presets():
    assert MODULES["4-3-3"] == (1, 4, 3, 3)
    assert MODULES["3-5-2"] == (1, 3, 5, 2)
    assert MODULES["4-4-2"] == (1, 4, 4, 2)
    assert MODULES["3-4-3"] == (1, 3, 4, 3)


def test_slot_need_zero_when_group_full():
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, _league([]), FULL_SLOTS, [], "4-3-3")
    assert utility.slot_need == 0.0


def test_slot_need_zero_when_group_closed():
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    slots = dict(FULL_SLOTS, A=0)
    utility = utility_score(player, _league([]), slots, [], "4-3-3")
    assert utility.slot_need == 0.0


def test_slot_need_open_group():
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    slots = {RoleGroup.P: 2, RoleGroup.D: 8, RoleGroup.C: 8, RoleGroup.A: 1}
    utility = utility_score(player, _league([]), slots, [], "4-3-3")
    expected = 1 - 1 / ((3 / 11) * 19)
    assert utility.slot_need == pytest.approx(expected)


def test_module_changes_slot_need():
    player = _player("D1", Role.DC, "A", "/p/d1")
    slots = {RoleGroup.P: 1, RoleGroup.D: 2, RoleGroup.C: 5, RoleGroup.A: 0}
    u433 = utility_score(player, _league([]), slots, [], "4-3-3")
    u343 = utility_score(player, _league([]), slots, [], "3-4-3")
    assert u433.slot_need > u343.slot_need


def test_calendar_ease_is_fraction_of_easy_opponents():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("2", "Debole2", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("A", "Atalanta", None, None, ("1", "2", "3")),
        ]
    )
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, league, FULL_SLOTS, [], "4-3-3")
    assert utility.calendar_ease == pytest.approx(2 / 3)
    assert utility.slot_need == 0.0


def test_coverage_neutral_without_own_players():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("A", "Atalanta", None, None, ("1",)),
        ]
    )
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, league, FULL_SLOTS, [], "4-3-3")
    assert utility.coverage == 0.5


def test_coverage_penalized_when_own_player_covers_same_week():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("A", "Atalanta", None, None, ("1",)),
            _team("B", "Bologna", None, None, ("1",)),
        ]
    )
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    own = [_player("PC2", Role.PC, "B", "/p/pc2")]
    utility = utility_score(player, league, FULL_SLOTS, own, "4-3-3")
    assert utility.coverage == 0.0


def test_coverage_full_when_own_player_faces_hard_opponent():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("A", "Atalanta", None, None, ("1",)),
            _team("B", "Bologna", None, None, ("3",)),
        ]
    )
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    own = [_player("PC2", Role.PC, "B", "/p/pc2")]
    utility = utility_score(player, league, FULL_SLOTS, own, "4-3-3")
    assert utility.coverage == pytest.approx(1.0)


def test_opponent_outlook_flags_and_strength():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("A", "Atalanta", None, None, ("1", "3")),
        ]
    )
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    outlook = opponent_outlook(player, league)
    assert [(opp.team_name, opp.easy) for opp in outlook] == [("Debole", True), ("Forte", False)]
    assert outlook[0].strength == 0.5


def test_opponent_outlook_empty_without_data():
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    assert opponent_outlook(player, _league([])) == ()


def test_defender_benchmark_is_attack_strength():
    league = _league(
        [
            _team("1", "AttaccoDebole", 0.5, 1.0, ()),
            _team("A", "Atalanta", None, None, ("1",)),
        ]
    )
    player = _player("D1", Role.DC, "A", "/p/d1")
    outlook = opponent_outlook(player, league)
    assert outlook[0].easy is True
    assert outlook[0].strength == 0.5


def test_full_calendar_counts_opponents_beyond_five_weeks():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("A", "Atalanta", None, None, ("3",)),
        ]
    )
    calendar = {
        "A": TeamCalendar("A", ("3", "3", "3", "3", "3", "3", "3", "1")),
    }
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, league, FULL_SLOTS, [], "4-3-3", calendar)
    assert utility.calendar_ease == pytest.approx(1 / 8)


def test_unknown_strength_is_neutral():
    league = _league([])
    calendar = {"A": TeamCalendar("A", ("1", "1", "1"))}
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, league, FULL_SLOTS, [], "4-3-3", calendar)
    outlook = opponent_outlook(player, league, calendar)
    assert all(opp.easy is None for opp in outlook)
    assert utility.calendar_ease == 0.5


def test_proxy_strengths_fallback_preseason():
    league = _league([], gf=None, ga=None)
    calendar = {"A": TeamCalendar("A", ("1", "3"))}
    strengths = {"1": 50.0, "3": 200.0, "A": 120.0}
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    outlook = opponent_outlook(player, league, calendar, strengths)
    assert [(opp.team_name, opp.easy) for opp in outlook] == [
        ("1", True),
        ("3", False),
    ]
    assert outlook[0].strength == 50.0


def test_team_strengths_from_players():
    players = [
        _player("P1", Role.PC, "A", "/p/p1"),
        _player("P2", Role.PC, "A", "/p/p2"),
        _player("P3", Role.PC, "B", "/p/p3"),
        Player(
            name="NoFVM",
            role=Role.POR,
            team_id="C",
            team_code="TC",
            team_name="Team",
            quote=Quote(qi=5, qa=5, fvm=None),
            url="/p/nofvm",
        ),
    ]
    strengths = team_strengths_from_players(players)
    assert strengths["A"] == 100.0
    assert strengths["B"] == 100.0
    assert "C" not in strengths


def test_coverage_penalized_on_full_calendar():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("A", "Atalanta", None, None, ("3",)),
            _team("B", "Bologna", None, None, ("3",)),
        ]
    )
    calendar = {
        "A": TeamCalendar("A", ("3", "3", "3", "3", "3", "3", "3", "1")),
        "B": TeamCalendar("B", ("1", "1", "1", "1", "1", "1", "1", "1")),
    }
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    own = [_player("PC2", Role.PC, "B", "/p/pc2")]
    utility = utility_score(player, league, FULL_SLOTS, own, "4-3-3", calendar)
    assert utility.coverage == pytest.approx(0.0)
