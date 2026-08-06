"""Test delle funzioni guida (M8-T4): rosa per copertura, greedy, candidati.

Lega sintetica costruita a mano: nessuna rete, nessun filesystem. Il
modello MILP usa slot ridotti per rendere i test veloci e determinati.
"""

from entities import Player, Quote, Role, RoleGroup
from guide import (
    beam_combinations,
    coverage_completion,
    greedy_cover,
    k_best_rosters,
    optimize_roster_coverage,
    position_candidates,
    top_candidates,
)
from projection import LeagueContext, TeamContext
from utility import CalendarWeek, TeamCalendar, formation_positions

FULL_SLOTS = {
    RoleGroup.P: 2,
    RoleGroup.D: 8,
    RoleGroup.C: 8,
    RoleGroup.A: 7,
}


def _player(name: str, role: Role, team_id: str, url: str, fvm: int = 100) -> Player:
    return Player(
        name=name,
        role=role,
        team_id=team_id,
        team_code="TC",
        team_name="Team",
        quote=Quote(qi=10, qa=10, fvm=fvm),
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
    return TeamCalendar(
        team_id=team_id,
        weeks=tuple(CalendarWeek(matchweek=mw, opponent_id=opp) for mw, opp in weeks),
    )


def _coverage_scenario() -> tuple[list[Player], LeagueContext, dict[str, TeamCalendar]]:
    """Una squadra facile (A) e una difficile (B), 1 giocatore per gruppo."""
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
        ]
    )
    calendar = {
        "A": _calendar("A", (4, "1"), (5, "1")),
        "B": _calendar("B", (4, "3"), (5, "3")),
    }
    players = [
        _player("POR_A", Role.POR, "A", "/p/pora"),
        _player("DC_A", Role.DC, "A", "/p/dca"),
        _player("C_A", Role.C, "A", "/p/ca", fvm=100),
        _player("PC_A", Role.PC, "A", "/p/pca", fvm=100),
        _player("POR_B", Role.POR, "B", "/p/porb"),
        _player("DC_B", Role.DC, "B", "/p/dcb"),
        _player("C_B", Role.C, "B", "/p/cb", fvm=300),
        _player("PC_B", Role.PC, "B", "/p/pcb", fvm=300),
    ]
    return players, league, calendar


SLOTS_ONE = {RoleGroup.P: 1, RoleGroup.D: 1, RoleGroup.C: 1, RoleGroup.A: 1}


def test_roster_coverage_prefers_coverage_over_points():
    players, league, calendar = _coverage_scenario()
    squad = optimize_roster_coverage(players, league, calendar, budget=200, slots=SLOTS_ONE)
    assert squad.status == "Optimal"
    urls = {player.url for player in squad.selected}
    assert "/p/ca" in urls
    assert "/p/cb" not in urls
    assert squad.covered_weeks == (4, 5)
    assert squad.total_cost == 40


def test_roster_coverage_budget_constraint():
    players, league, calendar = _coverage_scenario()
    squad = optimize_roster_coverage(players, league, calendar, budget=1, slots=SLOTS_ONE)
    assert squad.status == "Infeasible"


def test_roster_coverage_full_slots_without_players_infeasible():
    players, league, calendar = _coverage_scenario()
    squad = optimize_roster_coverage(players, league, calendar, budget=500, slots=FULL_SLOTS)
    assert squad.status == "Infeasible"


def test_greedy_picks_most_covering_first():
    players, league, calendar = _coverage_scenario()
    picks = greedy_cover([p for p in players if p.role is Role.C], league, calendar)
    assert [pick.player.url for pick in picks] == ["/p/ca", "/p/cb"]
    assert picks[0].covered_weeks == (4, 5)
    assert picks[0].cost == 10
    assert picks[1].added_weeks == ()
    assert picks[1].covered_weeks == (4, 5)


def test_greedy_tie_break_by_points():
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("2", "Debole2", 1.0, 0.5, ()),
        ]
    )
    calendar = {
        "A": _calendar("A", (4, "1")),
        "B": _calendar("B", (4, "2")),
    }
    weak = _player("C_WEAK", Role.C, "A", "/p/cw", fvm=100)
    strong = _player("C_STRONG", Role.C, "B", "/p/cs", fvm=300)
    picks = greedy_cover([weak, strong], league, calendar)
    assert picks[0].player.url == "/p/cs"


def test_top_candidates_rank_by_coverage_then_points():
    players, league, calendar = _coverage_scenario()
    candidates = top_candidates([p for p in players if p.role is Role.C], league, calendar, limit=2)
    assert [player.url for player in candidates] == ["/p/ca", "/p/cb"]


def test_top_candidates_limited():
    players, league, calendar = _coverage_scenario()
    candidates = top_candidates([p for p in players if p.role is Role.C], league, calendar, limit=1)
    assert [player.url for player in candidates] == ["/p/ca"]


def test_k_best_rosters_excludes_previous_xis():
    players, league, calendar = _coverage_scenario()
    squads = k_best_rosters("4-3-3", players, league, calendar, budget=200, k=3, slots=SLOTS_ONE)
    assert len(squads) >= 2
    first_xi = {
        slot.player.url
        for line in formation_positions("4-3-3", squads[0].selected)
        for slot in line.positions
        if slot.player is not None
    }
    second_selected = {player.url for player in squads[1].selected}
    assert not first_xi & second_selected


def test_k_best_rosters_stops_when_pool_exhausted():
    players, league, calendar = _coverage_scenario()
    squads = k_best_rosters("4-3-3", players, league, calendar, budget=200, k=10, slots=SLOTS_ONE)
    assert len(squads) < 10
    assert all(squad.status == "Optimal" for squad in squads)


def test_position_candidates_returns_all_sorted():
    players, league, calendar = _coverage_scenario()
    candidates = position_candidates(
        Role.C, [p for p in players if p.role is Role.C], league, calendar
    )
    assert len(candidates) == 2
    assert [player.url for player in candidates] == ["/p/ca", "/p/cb"]


def test_position_candidates_accepts_multi_role():
    players, league, calendar = _coverage_scenario()
    w_a = Player(
        name="W_A",
        role=Role.W,
        team_id="A",
        team_code="TC",
        team_name="Team",
        quote=Quote(qi=10, qa=10, fvm=100),
        url="/p/wa",
        roles=(Role.W, Role.A),
    )
    candidates = position_candidates(Role.A, [w_a], league, calendar)
    assert [player.url for player in candidates] == ["/p/wa"]


def test_beam_combinations_ranks_by_coverage():
    players, league, calendar = _coverage_scenario()
    c_candidates = [p for p in players if p.role is Role.C]
    a_candidates = [p for p in players if p.role is Role.PC]
    combos = beam_combinations([c_candidates, a_candidates], league, calendar, top=2)
    assert len(combos) == 2
    best = combos[0]
    assert {player.url for player in best.players} == {"/p/ca", "/p/pcb"}
    assert best.covered_weeks == (4, 5)
    assert best.cost == 20


def test_beam_combinations_skips_duplicate_players():
    w_a = Player(
        name="W_A",
        role=Role.W,
        team_id="A",
        team_code="TC",
        team_name="Team",
        quote=Quote(qi=10, qa=10, fvm=100),
        url="/p/wa",
        roles=(Role.W, Role.A),
    )
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("2", "Debole2", 1.0, 0.5, ()),
        ]
    )
    calendar = {
        "A": _calendar("A", (4, "1")),
        "B": _calendar("B", (4, "2")),
    }
    other = _player("PC_B", Role.PC, "B", "/p/pcb")
    combos = beam_combinations([[w_a, other], [w_a, other]], league, calendar, top=10)
    for combo in combos:
        urls = [player.url for player in combo.players]
        assert len(urls) == len(set(urls))


def _completion_scenario() -> tuple[list[Player], LeagueContext, dict[str, TeamCalendar]]:
    """A copre 4-5, B solo 4, C solo 5."""
    league = _league(
        [
            _team("1", "Debole", 1.0, 0.5, ()),
            _team("3", "Forte", 1.0, 1.5, ()),
        ]
    )
    calendar = {
        "A": _calendar("A", (4, "1"), (5, "1")),
        "B": _calendar("B", (4, "1"), (5, "3")),
        "C": _calendar("C", (4, "3"), (5, "1")),
        "D": _calendar("D", (4, "3"), (5, "3")),
    }
    players = [
        _player("PC_A", Role.PC, "A", "/p/pca"),
        _player("C_B", Role.C, "B", "/p/cb"),
        _player("DC_C", Role.DC, "C", "/p/dcc"),
        _player("POR_D", Role.POR, "D", "/p/pord"),
    ]
    return players, league, calendar


def test_coverage_completion_starts_from_player_weeks():
    players, league, calendar = _completion_scenario()
    player = next(p for p in players if p.url == "/p/cb")
    picks = coverage_completion(player, players, league, calendar)
    assert len(picks) == 1
    assert picks[0].player.url == "/p/pca"
    assert picks[0].added_weeks == (5,)
    assert picks[0].covered_weeks == (4, 5)


def test_coverage_completion_excludes_selected_player():
    players, league, calendar = _completion_scenario()
    player = next(p for p in players if p.url == "/p/pca")
    picks = coverage_completion(player, players, league, calendar)
    assert all(pick.player.url != player.url for pick in picks)
    assert picks == ()


def test_coverage_completion_stops_when_no_more_weeks():
    players, league, calendar = _completion_scenario()
    player = next(p for p in players if p.url == "/p/cb")
    picks = coverage_completion(player, [player, players[3]], league, calendar)
    assert picks == ()


def test_coverage_completion_respects_limit():
    players, league, calendar = _completion_scenario()
    player = next(p for p in players if p.url == "/p/cb")
    picks = coverage_completion(player, players, league, calendar, limit=1)
    assert len(picks) == 1
