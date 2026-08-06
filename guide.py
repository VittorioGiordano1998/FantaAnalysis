"""Guide per l'asta: rosa per copertura e combinazioni per ruolo (layer logic).

Pura computazione, nessun I/O. Il modello MILP seleziona la rosa completa
(2P-8D-8C-7A) tra i giocatori rimasti massimizzando le giornate con
partita facile coperte, con punti attesi e costo come criteri di
spareggio; greedy e candidati per ruolo alimentano i file guida (M8-T4).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import pulp

from entities import ROLE_GROUP, Player, RoleGroup
from optimize import ROSA_SLOTS
from projection import LeagueContext, project
from utility import TeamCalendar, opponent_outlook, remaining_weeks

WEEK_WEIGHT = 100_000.0
POINTS_WEIGHT = 100.0
COST_PENALTY = 0.01

_OPTIMAL = "Optimal"
_INFEASIBLE = "Infeasible"


@dataclass(frozen=True)
class CoverageSquad:
    """Rosa completa scelta per la copertura delle giornate facili."""

    selected: tuple[Player, ...]
    total_points: float
    total_cost: int
    covered_weeks: tuple[int, ...]
    status: str


@dataclass(frozen=True)
class GreedyPick:
    """Un passo della presa progressiva per copertura."""

    player: Player
    added_weeks: tuple[int, ...]
    covered_weeks: tuple[int, ...]
    cost: int


def optimize_roster_coverage(
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    *,
    budget: int = 500,
    slots: Mapping[RoleGroup, int] = ROSA_SLOTS,
) -> CoverageSquad:
    """Rosa completa che massimizza le giornate facili coperte.

    Obiettivo lessicografico: prima la copertura (una variabile per
    giornata rimanente, attiva se almeno un preso ha partita facile), poi i
    punti attesi, poi il costo minore. Vincoli: slot per gruppo e budget.

    Args:
        players: giocatori ancora disponibili (pool).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).
        budget: crediti disponibili.
        slots: slot di rosa per gruppo (default 2P-8D-8C-7A).

    Returns:
        `CoverageSquad` con status "Optimal" o "Infeasible".
    """
    weeks = remaining_weeks(league, calendar)
    easy_by_week: dict[int, list[Player]] = {week: [] for week in weeks}
    for player in players:
        for opp in opponent_outlook(player, league, calendar, team_strengths):
            if opp.easy is True and opp.matchweek in easy_by_week:
                easy_by_week[opp.matchweek].append(player)
    projections = {player.url: project(player, league).total_points for player in players}
    prices = {player.url: player.quote.qi or 0 for player in players}

    model = pulp.LpProblem("rosa_copertura", pulp.LpMaximize)
    variables = {
        player.url: model.add_variable(f"x_{index}", cat=pulp.LpBinary)
        for index, player in enumerate(players)
    }
    cover = {week: model.add_variable(f"c_{week}", cat=pulp.LpBinary) for week in weeks}
    objective = pulp.lpSum(WEEK_WEIGHT * cover[week] for week in weeks)
    objective += POINTS_WEIGHT * pulp.lpSum(
        projections[player.url] * variables[player.url] for player in players
    )
    objective -= COST_PENALTY * pulp.lpSum(
        prices[player.url] * variables[player.url] for player in players
    )
    model += objective
    model += (
        pulp.lpSum(prices[player.url] * variables[player.url] for player in players) <= budget,
        "budget",
    )
    for group, count in slots.items():
        model += (
            pulp.lpSum(
                variables[player.url] for player in players if ROLE_GROUP[player.role] is group
            )
            == count,
            f"slot_{group.value}",
        )
    for week in weeks:
        model += (
            cover[week] <= pulp.lpSum(variables[player.url] for player in easy_by_week[week]),
            f"cover_{week}",
        )
    model.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[model.status]
    if status != _OPTIMAL:
        return CoverageSquad((), 0.0, 0, (), _INFEASIBLE)
    selected = tuple(player for player in players if variables[player.url].value() > 0.5)
    covered = tuple(week for week in weeks if cover[week].value() > 0.5)
    return CoverageSquad(
        selected=selected,
        total_points=sum(projections[player.url] for player in selected),
        total_cost=sum(prices[player.url] for player in selected),
        covered_weeks=covered,
        status=_OPTIMAL,
    )


def greedy_cover(
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    limit: int | None = None,
) -> tuple[GreedyPick, ...]:
    """Presa progressiva: chi aggiunge più giornate facili non coperte.

    A parità di giornate aggiunte sceglie chi ha più punti attesi, poi chi
    costa meno. Utile per le combinazioni per ruolo (File 2).

    Args:
        players: giocatori candidati.
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata.
        limit: numero massimo di prese (None = tutti).

    Returns:
        Un `GreedyPick` per presa, con giornate coperte cumulative e costo.
    """
    covered: set[int] = set()
    remaining = list(players)
    picks: list[GreedyPick] = []
    cost = 0
    while remaining and (limit is None or len(picks) < limit):
        best: tuple[tuple, Player, frozenset[int]] | None = None
        for player in remaining:
            easy = frozenset(
                opp.matchweek
                for opp in opponent_outlook(player, league, calendar, team_strengths)
                if opp.easy is True
            )
            key = (
                -len(easy - covered),
                -project(player, league).total_points,
                player.quote.qi or 0,
            )
            if best is None or key < best[0]:
                best = (key, player, easy)
        if best is None:
            break
        _, player, easy = best
        remaining.remove(player)
        cost += player.quote.qi or 0
        added = tuple(sorted(easy - covered))
        covered |= easy
        picks.append(
            GreedyPick(
                player=player,
                added_weeks=added,
                covered_weeks=tuple(sorted(covered)),
                cost=cost,
            )
        )
    return tuple(picks)


def top_candidates(
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    limit: int = 3,
) -> tuple[Player, ...]:
    """I migliori candidati per copertura (facili, punti, costo minore)."""

    def key(player: Player) -> tuple:
        easy = sum(
            1
            for opp in opponent_outlook(player, league, calendar, team_strengths)
            if opp.easy is True
        )
        return (-easy, -project(player, league).total_points, player.quote.qi or 0)

    return tuple(sorted(players, key=key)[:limit])
