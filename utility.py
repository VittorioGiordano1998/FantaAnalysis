"""Utilità di acquisto per i consigli in asta (layer logic).

Pura computazione, nessun I/O: i dati arrivano come tipi condivisi. Il
punteggio di utilità (0..1) combina tre componenti a peso uguale: bisogno
di ruolo (slot residui vs modulo), facilità dei prossimi avversari e
copertura delle partite facili rispetto ai giocatori già presi della
propria squadra.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from entities import ROLE_GROUP, Player, RoleGroup
from projection import LeagueContext

NEXT_WEEKS = 5
DEFAULT_MODULE = "4-3-3"

MODULES: Mapping[str, tuple[int, int, int, int]] = {
    "4-3-3": (1, 4, 3, 3),
    "3-5-2": (1, 3, 5, 2),
    "4-4-2": (1, 4, 4, 2),
    "3-4-3": (1, 3, 4, 3),
}


@dataclass(frozen=True)
class OpponentOutlook:
    """Un avversario futuro con la sua forza e se è "facile" per il ruolo."""

    team_name: str
    strength: float | None
    easy: bool


@dataclass(frozen=True)
class UtilityScore:
    """Punteggio di utilità con le tre componenti (0..1 ciascuna)."""

    score: float
    slot_need: float
    calendar_ease: float
    coverage: float


def utility_score(
    player: Player,
    league: LeagueContext,
    slots_left: Mapping[RoleGroup, int],
    own_players: Sequence[Player],
    module: str = DEFAULT_MODULE,
) -> UtilityScore:
    """Utilità di acquisto del giocatore per la propria squadra (0..1).

    Media di tre componenti a peso uguale:
    - bisogno di ruolo dagli slot residui vs quota del modulo;
    - frazione dei prossimi `NEXT_WEEKS` avversari facili per il ruolo;
    - copertura aggiunta delle settimane facili rispetto a `own_players`.

    Args:
        player: giocatore da valutare (deve essere nel pool dei rimasti).
        league: contesto campionato (forze squadra + calendario).
        slots_left: slot di rosa residui per gruppo ruolo.
        own_players: giocatori già presi dalla propria squadra.
        module: preset modulo (chiave di `MODULES`).

    Returns:
        Punteggio complessivo e componenti, ciascuna in [0, 1].
    """
    outlook = opponent_outlook(player, league)
    ease = [opp.easy for opp in outlook]
    slot_need = _slot_need(player, slots_left, module)
    calendar_ease = _mean(ease) if ease else 0.5
    coverage = _coverage(ease, player, league, own_players)
    score = (slot_need + calendar_ease + coverage) / 3.0
    return UtilityScore(
        score=score,
        slot_need=slot_need,
        calendar_ease=calendar_ease,
        coverage=coverage,
    )


def opponent_outlook(player: Player, league: LeagueContext) -> tuple[OpponentOutlook, ...]:
    """I prossimi `NEXT_WEEKS` avversari con forza e flag "facile".

    Un avversario è facile per attaccanti e centrocampisti quando la sua
    difesa (gol subiti a partita) è sotto la media di lega; per difensori e
    portieri quando il suo attacco (gol fatti a partita) è sotto la media.

    Args:
        player: giocatore di cui si valuta il calendario.
        league: contesto campionato.

    Returns:
        Una `OpponentOutlook` per avversario (vuota se mancano i dati).
    """
    context = league.teams.get(player.team_id)
    if context is None or not context.upcoming_opponents:
        return ()
    outlook: list[OpponentOutlook] = []
    for opponent_id in context.upcoming_opponents[:NEXT_WEEKS]:
        opponent = league.teams.get(opponent_id)
        if opponent is None:
            continue
        strength = _opponent_strength(player, opponent)
        easy = _is_easy(strength, _league_benchmark(player, league))
        outlook.append(
            OpponentOutlook(
                team_name=opponent.team_name,
                strength=strength,
                easy=easy,
            )
        )
    return tuple(outlook)


def _slot_need(
    player: Player,
    slots_left: Mapping[RoleGroup, int],
    module: str,
) -> float:
    """Bisogno di ruolo: 1 se il gruppo è scoperto, 0 se saturo.

    Il bisogno cresce quando gli slot residui del gruppo sono sotto la
    quota attesa dal modulo sugli slot totali rimasti.
    """
    group = ROLE_GROUP[player.role]
    left = slots_left.get(group, 0)
    if left <= 0:
        return 0.0
    counts = MODULES.get(module, MODULES[DEFAULT_MODULE])
    total_left = sum(slots_left.values())
    if total_left <= 0:
        return 0.0
    expected = counts[_GROUP_INDEX[group]] / sum(counts) * total_left
    if expected <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - left / expected))


def _coverage(
    ease: list[bool],
    player: Player,
    league: LeagueContext,
    own_players: Sequence[Player],
) -> float:
    """Copertura aggiunta nelle settimane facili del giocatore.

    Per ogni settimana facile del giocatore il guadagno è la quota di
    giocatori propri che quella settimana NON giocano già un avversario
    facile; media sulle settimane facili (0.5 neutro se nessuna).
    """
    own_easy, own_present = _own_coverage_by_week(own_players, league)
    gains = [
        1.0 - own_easy[week] / own_present[week]
        for week, is_easy in enumerate(ease)
        if is_easy and own_present[week] > 0
    ]
    if not gains:
        return 0.5
    return max(0.0, min(1.0, sum(gains) / len(gains)))


def _own_coverage_by_week(
    own_players: Sequence[Player],
    league: LeagueContext,
) -> tuple[list[int], list[int]]:
    """Per ognuna delle prossime settimane: giocatori propri con avversario
    facile (e totale dei presenti)."""
    easy_counts = [0] * NEXT_WEEKS
    present = [0] * NEXT_WEEKS
    for own in own_players:
        outlook = opponent_outlook(own, league)
        for week, opp in enumerate(outlook):
            if week >= NEXT_WEEKS:
                break
            present[week] += 1
            if opp.easy:
                easy_counts[week] += 1
    return easy_counts, present


def _opponent_strength(player: Player, opponent) -> float | None:
    """Metrica di forza rilevante: attacco o difesa avversaria per ruolo."""
    if ROLE_GROUP[player.role] in (RoleGroup.A, RoleGroup.C):
        return opponent.ga_per_match
    return opponent.gf_per_match


def _league_benchmark(player: Player, league: LeagueContext) -> float | None:
    """Media di lega rilevante (gol subiti o fatti) per il ruolo."""
    if ROLE_GROUP[player.role] in (RoleGroup.A, RoleGroup.C):
        return league.league_ga_per_match
    return league.league_gf_per_match


def _is_easy(strength: float | None, benchmark: float | None) -> bool:
    """Vero se l'avversario è sotto la media di lega (dati assenti → False)."""
    if strength is None or benchmark is None or benchmark <= 0:
        return False
    return strength < benchmark


def _mean(values: list[bool]) -> float:
    """Frazione di True, 0.0 se vuota."""
    if not values:
        return 0.0
    return sum(values) / len(values)


_GROUP_INDEX: Mapping[RoleGroup, int] = {
    RoleGroup.P: 0,
    RoleGroup.D: 1,
    RoleGroup.C: 2,
    RoleGroup.A: 3,
}
