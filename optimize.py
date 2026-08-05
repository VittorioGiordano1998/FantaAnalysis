"""Ottimizzazione della rosa ottimale con PuLP (layer logic, ADR-0003).

Pura computazione, nessun I/O: i dati arrivano come tipi condivisi. Il
modello massimizza i punti proiettati (ADR-0002) sui soli giocatori rimasti,
con vincoli di budget e slot per gruppo; il limite di spesa per giocatore è
il più grande prezzo a cui forzare il giocatore in rosa non peggiora la rosa
ottimale di base.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pulp

from entities import ROLE_GROUP, Player, RoleGroup
from projection import LeagueContext, project

DEFAULT_BUDGET = 500
ROSA_SLOTS: Mapping[RoleGroup, int] = {
    RoleGroup.P: 2,
    RoleGroup.D: 8,
    RoleGroup.C: 8,
    RoleGroup.A: 7,
}
PRICE_FIELDS = ("qi", "qa")

_OPTIMAL = "Optimal"
_INFEASIBLE = "Infeasible"


@dataclass(frozen=True)
class SquadResult:
    """Rosa ottimale: giocatori scelti, punti e costo totali, stato."""

    selected: tuple[Player, ...]
    total_points: float
    total_cost: int
    budget: int
    status: str


@dataclass(frozen=True)
class SpendingLimit:
    """Prezzo massimo consigliato per un giocatore (ADR-0003)."""

    player_url: str
    max_price: int
    baseline_points: float
    forced_points: float
    status: str


def optimize_squad(
    players: Sequence[Player],
    league: LeagueContext,
    *,
    budget: int = DEFAULT_BUDGET,
    slots: Mapping[RoleGroup, int] = ROSA_SLOTS,
    taken_urls: frozenset[str] = frozenset(),
    price_field: str = "qi",
) -> SquadResult:
    """Rosa ottimale tra i giocatori rimasti (ADR-0003).

    Args:
        players: tutti i giocatori del listone.
        league: contesto campionato per le proiezioni (ADR-0002).
        budget: crediti disponibili.
        slots: slot per gruppo ruolo (default rosa 2P-8D-8C-7A).
        taken_urls: URL dei giocatori già presi all'asta (esclusi dal pool).
        price_field: "qi" (default) o "qa" (fallback QI se assente).

    Returns:
        `SquadResult` con status "Optimal" o "Infeasible" (mai eccezioni
        per pool/budget non realizzabili).
    """
    if price_field not in PRICE_FIELDS:
        raise ValueError(f"price_field deve essere in {PRICE_FIELDS}")
    pool = [p for p in players if p.url not in taken_urls]
    projections = {p.url: project(p, league).total_points for p in pool}
    prices = {p.url: _price(p, price_field) for p in pool}
    model, variables = _build_model(pool, projections, prices, budget, slots)
    return _solve(model, variables, pool, prices, budget)


def spending_limit(
    player: Player,
    players: Sequence[Player],
    league: LeagueContext,
    *,
    budget: int = DEFAULT_BUDGET,
    slots: Mapping[RoleGroup, int] = ROSA_SLOTS,
    taken_urls: frozenset[str] = frozenset(),
    price_field: str = "qi",
) -> SpendingLimit:
    """Prezzo massimo consigliato per `player` (ADR-0003).

    È il più grande `pr` intero in [0, budget] tale che l'ottimo con
    `player` forzato in rosa (budget `budget − pr`) valga almeno quanto
    l'ottimo di base senza `player` (baseline).

    Args:
        player: giocatore da valutare (deve essere nel pool dei rimasti).
        players: tutti i giocatori del listone.
        league: contesto campionato per le proiezioni.
        budget: crediti disponibili.
        slots: slot per gruppo ruolo.
        taken_urls: URL dei giocatori già presi (esclusi dal pool).
        price_field: "qi" (default) o "qa".

    Returns:
        `SpendingLimit` con `max_price` in [0, budget]; status "Optimal"
        oppure "Infeasible" se la rosa di base non è realizzabile.
    """
    pool = [p for p in players if p.url not in taken_urls]
    if player.url not in {p.url for p in pool}:
        raise ValueError("player non presente nel pool dei rimasti")
    projections = {p.url: project(p, league).total_points for p in pool}
    prices = {p.url: _price(p, price_field) for p in pool}

    base = optimize_squad(
        players,
        league,
        budget=budget,
        slots=slots,
        taken_urls=taken_urls,
        price_field=price_field,
    )
    if base.status != _OPTIMAL:
        return SpendingLimit(player.url, 0, 0.0, 0.0, _INFEASIBLE)

    if any(p.url == player.url for p in base.selected):
        pool_without = [p for p in pool if p.url != player.url]
        model, variables = _build_model(pool_without, projections, prices, budget, slots)
        baseline = _solve(model, variables, pool_without, prices, budget).total_points
    else:
        baseline = base.total_points

    max_price = _binary_search_max_price(pool, player, baseline, projections, prices, budget, slots)
    forced = _forced_points(pool, player, max_price, projections, prices, budget, slots)
    return SpendingLimit(player.url, max_price, baseline, forced, _OPTIMAL)


def _build_model(
    pool: Sequence[Player],
    projections: Mapping[str, float],
    prices: Mapping[str, int],
    budget: int,
    slots: Mapping[RoleGroup, int],
) -> tuple[pulp.LpProblem, dict[str, pulp.LpVariable]]:
    """Modello PuLP: massimizza punti, vincoli budget e slot (ADR-0003)."""
    model = pulp.LpProblem("rosa_ottimale", pulp.LpMaximize)
    variables: dict[str, pulp.LpVariable] = {
        p.url: model.add_variable(f"x_{idx}", cat=pulp.LpBinary) for idx, p in enumerate(pool)
    }
    model += pulp.lpSum(projections[p.url] * variables[p.url] for p in pool)
    model += (
        pulp.lpSum(prices[p.url] * variables[p.url] for p in pool) <= budget,
        "budget",
    )
    for group, slot in slots.items():
        model += (
            pulp.lpSum(variables[p.url] for p in pool if ROLE_GROUP[p.role] is group) == slot,
            f"slot_{group.value}",
        )
    return model, variables


def _solve(
    model: pulp.LpProblem,
    variables: Mapping[str, pulp.LpVariable],
    pool: Sequence[Player],
    prices: Mapping[str, int],
    budget: int,
) -> SquadResult:
    """Risolve il modello e impacchetta il risultato (mai eccezioni)."""
    model.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[model.status]
    if status != _OPTIMAL:
        return SquadResult(
            selected=(), total_points=0.0, total_cost=0, budget=budget, status=status
        )
    selected = tuple(p for p in pool if variables[p.url].value() > 0.5)
    return SquadResult(
        selected=selected,
        total_points=pulp.value(model.objective),
        total_cost=sum(prices[p.url] for p in selected),
        budget=budget,
        status=_OPTIMAL,
    )


def _forced_points(
    pool: Sequence[Player],
    player: Player,
    price: int,
    projections: Mapping[str, float],
    prices: Mapping[str, int],
    budget: int,
    slots: Mapping[RoleGroup, int],
) -> float:
    """Ottimo con `player` forzato in rosa e budget `budget − price`.

    Returns:
        Punti dell'ottimo, oppure −inf se il modello è irrealizzabile.
    """
    model, variables = _build_model(pool, projections, prices, budget - price, slots)
    model += variables[player.url] == 1, "forced"
    model.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[model.status] != _OPTIMAL:
        return -math.inf
    return pulp.value(model.objective)


def _binary_search_max_price(
    pool: Sequence[Player],
    player: Player,
    baseline: float,
    projections: Mapping[str, float],
    prices: Mapping[str, int],
    budget: int,
    slots: Mapping[RoleGroup, int],
) -> int:
    """Più grande `pr` con forced_points(pr) ≥ baseline (ADR-0003)."""
    low, high = 0, budget
    if _forced_points(pool, player, high, projections, prices, budget, slots) >= baseline:
        return high
    if _forced_points(pool, player, low, projections, prices, budget, slots) < baseline:
        return 0
    while low < high:
        mid = (low + high + 1) // 2
        if _forced_points(pool, player, mid, projections, prices, budget, slots) >= baseline:
            low = mid
        else:
            high = mid - 1
    return low


def _price(player: Player, price_field: str) -> int:
    """Prezzo del giocatore (QA con fallback QI; assente → 0)."""
    quote = player.quote
    value = getattr(quote, price_field)
    if value is None and price_field == "qa":
        value = quote.qi
    return value or 0
