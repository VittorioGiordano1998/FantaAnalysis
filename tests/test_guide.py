"""Test delle funzioni guida (M8-T4): rosa per copertura, greedy, candidati.

Lega sintetica costruita a mano: nessuna rete, nessun filesystem. Il
modello MILP usa slot ridotti per rendere i test veloci e determinati.
"""

from entities import Player, Quote, Role, RoleGroup
from guide import greedy_cover, optimize_roster_coverage, top_candidates
from projection import LeagueContext, TeamContext
from utility import CalendarWeek, TeamCalendar

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
