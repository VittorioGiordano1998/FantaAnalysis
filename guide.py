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

from entities import ROLE_GROUP, Player, Role, RoleGroup
from optimize import ROSA_SLOTS
from projection import LeagueContext, project
from utility import (
    TeamCalendar,
    formation_positions,
    opponent_outlook,
    player_roles,
    remaining_weeks,
)

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


@dataclass(frozen=True)
class LineCombination:
    """Una combinazione per una riga: un giocatore per posizione."""

    players: tuple[Player, ...]
    covered_weeks: tuple[int, ...]
    points: float
    cost: int


def k_best_rosters(
    module: str,
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    *,
    budget: int = 500,
    k: int = 10,
    slots: Mapping[RoleGroup, int] = ROSA_SLOTS,
) -> tuple[CoverageSquad, ...]:
    """Le k migliori rose per il modulo, con esclusione progressiva dei top.

    L'alternativa n esclude dal pool i titolari (XI del template del
    modulo) delle alternative 1..n-1: se i top non sono disponibili in
    asta, questa è la migliore rosa rimasta. La rosa resta la stessa per
    tutte le alternative finché il pool lo consente.

    Args:
        module: preset modulo (per estrarre l'XI da escludere).
        players: giocatori ancora disponibili (pool).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).
        budget: crediti disponibili.
        k: numero di alternative (default 10).
        slots: slot di rosa per gruppo (default 2P-8D-8C-7A).

    Returns:
        Una `CoverageSquad` per alternativa (meno se il pool si esaurisce).
    """
    excluded: set[str] = set()
    squads: list[CoverageSquad] = []
    previous: frozenset[str] = frozenset()
    for _ in range(k):
        pool = [player for player in players if player.url not in excluded]
        squad = optimize_roster_coverage(
            pool, league, calendar, team_strengths, budget=budget, slots=slots
        )
        if squad.status != _OPTIMAL:
            break
        selected_urls = frozenset(player.url for player in squad.selected)
        if selected_urls == previous:
            break
        previous = selected_urls
        squads.append(squad)
        xi = formation_positions(module, squad.selected)
        excluded |= {
            slot.player.url for line in xi for slot in line.positions if slot.player is not None
        }
    return tuple(squads)


def coverage_completion(
    player: Player,
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    limit: int | None = 12,
    budget: int | None = None,
    excluded: frozenset[str] = frozenset(),
    same_role: bool = True,
) -> tuple[GreedyPick, ...]:
    """Chi prendere (oltre a `player`) per coprire le giornate facili.

    Greedy: parte dalle giornate facili di `player` e aggiunge a ogni passo
    il giocatore rimasto (esclusi `player` e `excluded`) che copre più
    giornate non ancora coperte (a parità, più punti, poi costo minore);
    con `budget` considera solo i giocatori che ci stanno nei crediti
    rimanenti. Si ferma quando tutte le giornate rimanenti sono coperte,
    quando nessuno aggiunge più nulla, quando il budget non basta più o al
    raggiungimento di `limit` prese.

    Args:
        player: giocatore cercato (già nel pool dei rimasti).
        players: giocatori ancora disponibili (pool).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).
        limit: numero massimo di suggerimenti (default 12).
        budget: credito massimo spendibile complessivo (None = illimitato).
        excluded: URL da escludere dal pool (es. alternative precedenti).
        same_role: se True (default) considera solo giocatori che condividono
            almeno un ruolo con `player` (multiruolo incluso).

    Returns:
        I `GreedyPick` ordinati di presa, con costi e coperte cumulative.
    """
    covered: set[int] = set(
        opp.matchweek
        for opp in opponent_outlook(player, league, calendar, team_strengths)
        if opp.easy is True
    )
    player_role_set = set(player_roles(player))
    pool = [
        candidate
        for candidate in players
        if candidate.url != player.url
        and candidate.url not in excluded
        and (not same_role or player_role_set & set(player_roles(candidate)))
    ]
    picks: list[GreedyPick] = []
    cost = 0
    while pool and (limit is None or len(picks) < limit):
        best: tuple[tuple, Player, frozenset[int]] | None = None
        for candidate in pool:
            price = candidate.quote.qi or 0
            if budget is not None and cost + price > budget:
                continue
            easy = frozenset(
                opp.matchweek
                for opp in opponent_outlook(candidate, league, calendar, team_strengths)
                if opp.easy is True
            )
            key = (
                -len(easy - covered),
                -project(candidate, league).total_points,
                price,
            )
            if best is None or key < best[0]:
                best = (key, candidate, easy)
        if best is None:
            break
        _, candidate, easy = best
        added = easy - covered
        if not added:
            break
        pool.remove(candidate)
        cost += candidate.quote.qi or 0
        covered |= easy
        picks.append(
            GreedyPick(
                player=candidate,
                added_weeks=tuple(sorted(added)),
                covered_weeks=tuple(sorted(covered)),
                cost=cost,
            )
        )
    return tuple(picks)


def coverage_completions(
    player: Player,
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    *,
    limit: int | None = 12,
    budget: int | None = None,
    k: int = 5,
) -> tuple[tuple[GreedyPick, ...], ...]:
    """K alternative di copertura per il giocatore cercato.

    L'alternativa n esclude i suggeriti delle alternative precedenti: se i
    primi non sono disponibili in asta, ecco la migliore combinazione
    rimasta.

    Args:
        player: giocatore cercato (già nel pool dei rimasti).
        players: giocatori ancora disponibili (pool).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).
        limit: numero massimo di suggerimenti per alternativa.
        budget: credito massimo spendibile complessivo (None = illimitato).
        k: numero di alternative (default 5).

    Returns:
        Una tupla di `GreedyPick` per alternativa (meno se il pool si
        esaurisce o non ci sono più coperture).
    """
    excluded: set[str] = set()
    completions: list[tuple[GreedyPick, ...]] = []
    for _ in range(k):
        picks = coverage_completion(
            player,
            players,
            league,
            calendar,
            team_strengths,
            limit=limit,
            budget=budget,
            excluded=frozenset(excluded),
        )
        if not picks:
            break
        completions.append(picks)
        excluded |= {pick.player.url for pick in picks}
    return tuple(completions)


def position_candidates(
    role: Role,
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
) -> tuple[Player, ...]:
    """Tutti i giocatori validi per il ruolo, senza soglia.

    Includono i multiruolo (`role` in `player_roles`); ordinati per
    giornate facili coperte, poi punti attesi, poi prezzo minore.

    Args:
        role: ruolo richiesto dalla posizione.
        players: giocatori candidati (es. il gruppo del modulo).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata.

    Returns:
        Tutti i giocatori validi, ordinati per copertura.
    """
    valid = [player for player in players if role in player_roles(player)]
    return top_candidates(valid, league, calendar, team_strengths, limit=len(valid))


def beam_combinations(
    positions: Sequence[Sequence[Player]],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    *,
    beam: int = 50,
    top: int = 50,
) -> tuple[LineCombination, ...]:
    """Le migliori combinazioni per una riga (beam search).

    Una combinazione ha un giocatore per posizione (senza duplicati);
    l'obiettivo è massimizzare le giornate facili coperte, poi i punti
    attesi, poi il costo minore.

    Args:
        positions: liste di candidati per posizione (già ordinate).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata.
        beam: larghezza del fascio (default 50).
        top: numero di combinazioni da restituire (default 50).

    Returns:
        Le migliori `LineCombination`, ordinate per copertura.
    """
    states: list[tuple[tuple[Player, ...], frozenset[int], float, int]] = [
        ((), frozenset(), 0.0, 0)
    ]
    for candidates in positions:
        easy_by_url = {
            player.url: frozenset(
                opp.matchweek
                for opp in opponent_outlook(player, league, calendar, team_strengths)
                if opp.easy is True
            )
            for player in candidates
        }
        points_by_url = {player.url: project(player, league).total_points for player in candidates}
        next_states: list[tuple[tuple[Player, ...], frozenset[int], float, int]] = []
        for players, covered, points, cost in states:
            taken_urls = {player.url for player in players}
            for player in candidates:
                if player.url in taken_urls:
                    continue
                easy = easy_by_url[player.url]
                next_states.append(
                    (
                        players + (player,),
                        covered | easy,
                        points + points_by_url[player.url],
                        cost + (player.quote.qi or 0),
                    )
                )
        next_states.sort(key=lambda state: (-len(state[1]), -state[2], state[3]))
        states = next_states[:beam]
    return tuple(
        LineCombination(
            players=players,
            covered_weeks=tuple(sorted(covered)),
            points=points,
            cost=cost,
        )
        for players, covered, points, cost in states[:top]
    )


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
