"""Test unitari del modello di ottimizzazione (ADR-0003).

Pool sintetici con punti proiettati deterministici (fanta_avg = punti/38,
contesto neutro): nessun I/O, nessuna rete.
"""

import pytest

from entities import Player, Quote, Role, RoleGroup, SeasonStats
from optimize import optimize_squad, spending_limit
from projection import LeagueContext

LEAGUE = LeagueContext(season="2026-27", current_matchweek=1, teams={})

SLOTS = {RoleGroup.P: 1, RoleGroup.D: 2, RoleGroup.C: 2, RoleGroup.A: 1}

# (url, ruolo, qi, punti attesi)
_POOL = [
    ("por1", Role.POR, 10, 50.0),
    ("d1", Role.DC, 10, 60.0),
    ("d2", Role.DD, 10, 55.0),
    ("d3", Role.DS, 5, 50.0),
    ("d4", Role.DS, 3, 40.0),
    ("c1", Role.C, 10, 60.0),
    ("c2", Role.M, 10, 55.0),
    ("c3", Role.T, 5, 50.0),
    ("a1", Role.PC, 15, 70.0),
    ("a2", Role.A, 10, 65.0),
]


def _player(url: str, role: Role, qi: int, points: float, *, qa: int | None = None) -> Player:
    stats = SeasonStats(played_matches=10, fanta_avg=points / 38.0)
    return Player(
        name=url,
        role=role,
        team_id="1",
        team_code="T",
        team_name="Team",
        quote=Quote(qi=qi, qa=qa, fvm=qi * 100),
        url=url,
        stats=stats,
    )


def _pool(*, qa: int | None = None) -> list[Player]:
    return [_player(url, role, qi, points, qa=qa) for url, role, qi, points in _POOL]


def test_squad_equals_slots_when_pool_fits():
    pool = [_player("por1", Role.POR, 10, 50.0), _player("d1", Role.DC, 10, 60.0)]
    result = optimize_squad(pool, LEAGUE, slots={RoleGroup.P: 1, RoleGroup.D: 1})
    assert result.status == "Optimal"
    assert {p.url for p in result.selected} == {"por1", "d1"}
    assert result.total_points == pytest.approx(110.0)
    assert result.total_cost == 20


def test_base_optimum_picks_highest_points_per_slot():
    result = optimize_squad(_pool(), LEAGUE, budget=500, slots=SLOTS)
    assert result.status == "Optimal"
    assert {p.url for p in result.selected} == {"por1", "d1", "d2", "c1", "c2", "a1"}
    assert result.total_points == pytest.approx(50 + 60 + 55 + 60 + 55 + 70)
    assert result.total_cost == 65


def test_budget_forces_cheaper_squad():
    result = optimize_squad(_pool(), LEAGUE, budget=45, slots=SLOTS)
    assert result.status == "Optimal"
    assert "a1" not in {p.url for p in result.selected}
    assert "a2" in {p.url for p in result.selected}
    assert result.total_cost == 43
    assert result.total_points == pytest.approx(50 + 90 + 110 + 65)


def test_taken_players_excluded():
    pool = _pool()
    taken = {pool[2].url}
    result = optimize_squad(pool, LEAGUE, budget=500, slots=SLOTS, taken_urls=frozenset(taken))
    assert result.status == "Optimal"
    assert "d2" not in {p.url for p in result.selected}


def test_infeasible_when_pool_too_small():
    pool = [_player("por1", Role.POR, 10, 50.0), _player("d1", Role.DC, 10, 60.0)]
    result = optimize_squad(pool, LEAGUE, slots={RoleGroup.P: 2, RoleGroup.D: 2})
    assert result.status == "Infeasible"
    assert result.selected == ()


def test_infeasible_when_budget_too_low():
    pool = _pool()
    result = optimize_squad(pool, LEAGUE, budget=20, slots=SLOTS)
    assert result.status == "Infeasible"


def test_invalid_price_field_raises():
    with pytest.raises(ValueError):
        optimize_squad(_pool(), LEAGUE, price_field="bogus")


def test_price_field_qa_uses_qa_price():
    pool = _pool(qa=None)
    pool[5] = _player("c1", Role.C, 10, 60.0, qa=1)
    result = optimize_squad(pool, LEAGUE, budget=500, slots=SLOTS, price_field="qa")
    assert result.status == "Optimal"
    assert result.total_cost == 65 - 9


def test_squad_preserves_pool_order():
    result = optimize_squad(_pool(), LEAGUE, budget=500, slots=SLOTS)
    urls = [p.url for p in result.selected]
    assert urls == sorted(urls, key=lambda u: [p[0] for p in _POOL].index(u))


def test_spending_limit_selected_player():
    pool = _pool()
    d1 = next(p for p in pool if p.url == "d1")
    base = optimize_squad(pool, LEAGUE, budget=500, slots=SLOTS)
    limit = spending_limit(d1, pool, LEAGUE, budget=500, slots=SLOTS)
    assert limit.status == "Optimal"
    assert limit.baseline_points < base.total_points
    assert limit.max_price == 445
    assert limit.forced_points >= limit.baseline_points


def test_spending_limit_non_selected_player_is_zero():
    pool = _pool()
    d4 = next(p for p in pool if p.url == "d4")
    limit = spending_limit(d4, pool, LEAGUE, budget=500, slots=SLOTS)
    assert limit.status == "Optimal"
    assert limit.max_price == 0


def test_spending_limit_infeasible_base():
    pool = [_player("por1", Role.POR, 10, 50.0), _player("d1", Role.DC, 10, 60.0)]
    limit = spending_limit(pool[1], pool, LEAGUE, slots={RoleGroup.P: 2, RoleGroup.D: 2})
    assert limit.status == "Infeasible"
    assert limit.max_price == 0
