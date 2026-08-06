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
    CalendarWeek,
    TeamCalendar,
    coverage_recommendations,
    coverage_suggestions,
    easy_candidates,
    formation_positions,
    missing_roles,
    opponent_outlook,
    team_strengths_from_players,
    utility_score,
    week_coverage,
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


def _calendar(team_id: str, *weeks: tuple[int, str]) -> TeamCalendar:
    """TeamCalendar da coppie (matchweek, opponent_id)."""
    return TeamCalendar(
        team_id=team_id,
        weeks=tuple(CalendarWeek(matchweek=mw, opponent_id=opp) for mw, opp in weeks),
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
        "A": _calendar("A", *((4 + i, "3") for i in range(7)), (11, "1")),
    }
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, league, FULL_SLOTS, [], "4-3-3", calendar)
    assert utility.calendar_ease == pytest.approx(1 / 8)


def test_unknown_strength_is_neutral():
    league = _league([])
    calendar = {"A": _calendar("A", (4, "1"), (5, "1"), (6, "1"))}
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    utility = utility_score(player, league, FULL_SLOTS, [], "4-3-3", calendar)
    outlook = opponent_outlook(player, league, calendar)
    assert all(opp.easy is None for opp in outlook)
    assert utility.calendar_ease == 0.5


def test_proxy_strengths_fallback_preseason():
    league = _league([], gf=None, ga=None)
    calendar = {"A": _calendar("A", (4, "1"), (5, "3"))}
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
        "A": _calendar("A", *((4 + i, "3") for i in range(7)), (11, "1")),
        "B": _calendar("B", *((4 + i, "1") for i in range(8))),
    }
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    own = [_player("PC2", Role.PC, "B", "/p/pc2")]
    utility = utility_score(player, league, FULL_SLOTS, own, "4-3-3", calendar)
    assert utility.coverage == pytest.approx(0.0)


def test_outlook_carries_matchweek():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("A", "Atalanta", None, None, ()),
        ]
    )
    calendar = {"A": _calendar("A", (4, "1"), (5, "3"))}
    player = _player("PC1", Role.PC, "A", "/p/pc1")
    outlook = opponent_outlook(player, league, calendar)
    assert [(opp.matchweek, opp.easy) for opp in outlook] == [(4, True), (5, False)]


def test_week_coverage_counts_easy_games_per_matchweek():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
        ]
    )
    calendar = {
        "B": _calendar("B", (4, "1"), (5, "3")),
        "C": _calendar("C", (4, "3"), (5, "1")),
    }
    own = [_player("PC2", Role.PC, "B", "/p/pc2"), _player("PC3", Role.PC, "C", "/p/pc3")]
    coverage = week_coverage(own, league, calendar)
    assert [(week.matchweek, week.easy_count, week.present_count) for week in coverage] == [
        (4, 1, 2),
        (5, 1, 2),
    ]
    assert not any(week.uncovered for week in coverage)


def test_week_coverage_flags_uncovered_weeks():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
        ]
    )
    calendar = {"B": _calendar("B", (4, "3"), (5, "3"))}
    own = [_player("PC2", Role.PC, "B", "/p/pc2")]
    coverage = week_coverage(own, league, calendar)
    assert [(week.matchweek, week.easy_count, week.uncovered) for week in coverage] == [
        (4, 0, True),
        (5, 0, True),
    ]


def test_week_coverage_empty_without_own_players():
    league = _league([])
    assert week_coverage([], league) == ()


def test_easy_candidates_filters_by_matchweek():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
            _team("4", "AttaccoDebole", 0.5, 1.5, ()),
        ]
    )
    calendar = {
        "A": _calendar("A", (4, "1"), (5, "3")),
        "B": _calendar("B", (4, "3"), (5, "1")),
        "C": _calendar("C", (4, "4"), (5, "3")),
    }
    pc_a = _player("PC_A", Role.PC, "A", "/p/pc_a")
    pc_b = _player("PC_B", Role.PC, "B", "/p/pc_b")
    dc_c = _player("DC_C", Role.DC, "C", "/p/dc_c")
    players = [pc_a, pc_b, dc_c]

    at_four = easy_candidates(4, players, league, calendar)
    assert {p.url for p in at_four} == {pc_a.url, dc_c.url}
    at_five = easy_candidates(5, players, league, calendar)
    assert {p.url for p in at_five} == {pc_b.url}


def _calendar_map() -> tuple[dict[str, TeamCalendar], LeagueContext]:
    """Lega sintetica: "1" debole (ga 0.5), "3" forte (ga 1.5)."""
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
        ]
    )
    calendar = {
        "A": _calendar("A", (4, "1"), (5, "3")),
        "B": _calendar("B", (4, "3"), (5, "3")),
        "C": _calendar("C", (4, "1"), (5, "1")),
        "D": _calendar("D", (4, "3"), (5, "1")),
    }
    return calendar, league


def test_coverage_suggestions_best_candidate_per_uncovered_week():
    calendar, league = _calendar_map()
    own = [_player("PC_B", Role.PC, "B", "/p/pc_b")]
    weak_a = _player("PC_A", Role.PC, "A", "/p/pc_a")
    strong_c = Player(
        name="PC_C",
        role=Role.PC,
        team_id="C",
        team_code="TC",
        team_name="Team",
        quote=Quote(qi=10, qa=10, fvm=200),
        url="/p/pc_c",
    )
    remaining = [weak_a, strong_c]
    suggestions = coverage_suggestions(own, remaining, league, calendar)
    assert [(sug.matchweek, sug.player.url) for sug in suggestions] == [
        (4, strong_c.url),
        (5, strong_c.url),
    ]
    assert suggestions[0].points > 0


def test_coverage_suggestions_empty_without_uncovered_weeks():
    calendar, league = _calendar_map()
    own = [_player("PC_C", Role.PC, "C", "/p/pc_c")]
    remaining = [_player("PC_A", Role.PC, "A", "/p/pc_a")]
    assert coverage_suggestions(own, remaining, league, calendar) == ()


def test_coverage_recommendations_rank_by_covered_weeks():
    calendar, league = _calendar_map()
    own = [_player("PC_B", Role.PC, "B", "/p/pc_b")]
    pc_c = _player("PC_C", Role.PC, "C", "/p/pc_c")
    pc_d = _player("PC_D", Role.PC, "D", "/p/pc_d")
    pc_a = _player("PC_A", Role.PC, "A", "/p/pc_a")
    recommendations = coverage_recommendations(own, [pc_c, pc_d, pc_a], league, calendar)
    assert [rec.player.url for rec in recommendations] == [
        pc_c.url,
        pc_d.url,
        pc_a.url,
    ]
    assert recommendations[0].covered_weeks == (4, 5)
    assert recommendations[1].covered_weeks == (5,)


def test_coverage_recommendations_empty_roster_targets_all_weeks():
    calendar, league = _calendar_map()
    pc_a = _player("PC_A", Role.PC, "A", "/p/pc_a")
    pc_c = _player("PC_C", Role.PC, "C", "/p/pc_c")
    recommendations = coverage_recommendations([], [pc_a, pc_c], league, calendar)
    assert [rec.player.url for rec in recommendations] == [pc_c.url, pc_a.url]
    assert recommendations[0].covered_weeks == (4, 5)
    assert recommendations[1].covered_weeks == (4,)


def _own_roster() -> list[Player]:
    """Rosa sintetica: 2 P, 5 D, 4 C, 4 A (ordine di presa)."""
    return [
        _player("P1", Role.POR, "A", "/p/p1"),
        _player("P2", Role.POR, "A", "/p/p2"),
        _player("D1", Role.DC, "A", "/p/d1"),
        _player("D2", Role.DD, "A", "/p/d2"),
        _player("D3", Role.DS, "A", "/p/d3"),
        _player("D4", Role.B, "A", "/p/d4"),
        _player("D5", Role.DC, "A", "/p/d5"),
        _player("C1", Role.C, "A", "/p/c1"),
        _player("C2", Role.M, "A", "/p/c2"),
        _player("C3", Role.E, "A", "/p/c3"),
        _player("C4", Role.T, "A", "/p/c4"),
        _player("A1", Role.PC, "A", "/p/a1"),
        _player("A2", Role.A, "A", "/p/a2"),
        _player("A3", Role.W, "A", "/p/a3"),
        _player("A4", Role.PC, "A", "/p/a4"),
    ]


def test_formation_positions_assigns_exact_roles():
    own = _own_roster()
    lines = formation_positions("4-3-3", own)
    assert [line.group for line in lines] == [
        RoleGroup.P,
        RoleGroup.D,
        RoleGroup.C,
        RoleGroup.A,
    ]
    d_line = lines[1]
    assert [slot.role for slot in d_line.positions] == [
        Role.DC,
        Role.DC,
        Role.DD,
        Role.DS,
    ]
    assert [slot.player.name for slot in d_line.positions] == ["D1", "D5", "D2", "D3"]
    assert missing_roles(d_line) == ()
    assert missing_roles(lines[0]) == ()


def test_formation_positions_repeated_roles_use_distinct_players():
    own = _own_roster()
    lines = formation_positions("4-4-2", own)
    a_line = lines[3]
    assert [slot.role for slot in a_line.positions] == [Role.PC, Role.PC]
    assert {slot.player.name for slot in a_line.positions} == {"A1", "A4"}


def test_formation_positions_flags_missing_roles():
    own = [
        _player("D1", Role.DC, "A", "/p/d1"),
        _player("D2", Role.DC, "A", "/p/d2"),
        _player("C1", Role.C, "A", "/p/c1"),
    ]
    lines = formation_positions("4-4-2", own)
    d_line = lines[1]
    assert missing_roles(d_line) == ("dd", "ds")
    assert [slot.player for slot in d_line.positions] == [
        own[0],
        own[1],
        None,
        None,
    ]
    c_line = lines[2]
    assert missing_roles(c_line) == ("e", "m", "e")


def test_formation_positions_empty_roster():
    lines = formation_positions("3-5-2", [])
    assert [len(line.positions) for line in lines] == [1, 3, 5, 2]
    assert all(slot.player is None for line in lines for slot in line.positions)
    assert missing_roles(lines[1]) == ("dc", "dc", "dc")
