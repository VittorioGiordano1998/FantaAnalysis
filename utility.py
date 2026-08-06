"""Utilità di acquisto per i consigli in asta (layer logic).

Pura computazione, nessun I/O: i dati arrivano come tipi condivisi. Il
punteggio di utilità (0..1) combina tre componenti a peso uguale: bisogno
di ruolo (slot residui vs modulo), facilità degli avversari su TUTTO il
calendario rimanente e copertura delle partite facili rispetto ai
giocatori già presi della propria squadra.

A stagione non iniziata (nessuna media di lega) la forza squadra è
stimata dal listone (`team_strengths_from_players`, media FVM per squadra);
i valori ignoti pesano 0.5 (neutro) nella media.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from entities import ROLE_GROUP, Player, Role, RoleGroup
from projection import LeagueContext, project

DEFAULT_MODULE = "4-3-3"

MODULES: Mapping[str, tuple[int, int, int, int]] = {
    "4-3-3": (1, 4, 3, 3),
    "3-5-2": (1, 3, 5, 2),
    "4-4-2": (1, 4, 4, 2),
    "3-4-3": (1, 3, 4, 3),
}

MODULE_POSITIONS: Mapping[str, tuple[tuple[str, ...], ...]] = {
    "4-3-3": (("por",), ("dc", "dc", "dd", "ds"), ("m", "c", "t"), ("pc", "a", "a")),
    "3-5-2": (("por",), ("dc", "dc", "dc"), ("e", "m", "c", "c", "e"), ("pc", "pc")),
    "4-4-2": (("por",), ("dc", "dc", "dd", "ds"), ("e", "m", "c", "e"), ("pc", "pc")),
    "3-4-3": (("por",), ("dc", "dc", "dc"), ("e", "m", "c", "e"), ("a", "pc", "a")),
}


@dataclass(frozen=True)
class CalendarWeek:
    """Un avversario futuro con la sua giornata di campionato."""

    matchweek: int
    opponent_id: str


@dataclass(frozen=True)
class TeamCalendar:
    """Calendario rimanente di una squadra, una settimana per giornata."""

    team_id: str
    weeks: tuple[CalendarWeek, ...]


@dataclass(frozen=True)
class OpponentOutlook:
    """Un avversario futuro con la sua forza e se è "facile" per il ruolo.

    `easy` è `None` quando la forza non è stimabile (nessun risultato e
    nessun proxy): in aggregato vale 0.5 (neutro).
    """

    team_name: str
    matchweek: int
    strength: float | None
    easy: bool | None


@dataclass(frozen=True)
class WeekCoverage:
    """Copertura di una giornata: facili coperte e giocatori propri presenti."""

    matchweek: int
    easy_count: int
    present_count: int

    @property
    def uncovered(self) -> bool:
        """Vero se la giornata è giocata da qualcuno ma senza partite facili."""
        return self.present_count > 0 and self.easy_count == 0


@dataclass(frozen=True)
class WeekSuggestion:
    """Miglior candidato rimasto per coprire una giornata scoperta."""

    matchweek: int
    player: Player
    points: float


@dataclass(frozen=True)
class CoverageRecommendation:
    """Giocatore rimasto che copre più giornate target (consiglio diretto)."""

    player: Player
    covered_weeks: tuple[int, ...]
    points: float


@dataclass(frozen=True)
class PositionSlot:
    """Una posizione del modulo: ruolo Mantra richiesto e titolare assegnato."""

    role: Role
    player: Player | None


@dataclass(frozen=True)
class FormationPosition:
    """Una riga della formazione (XI): gruppo e posizioni vincolate per ruolo."""

    group: RoleGroup
    positions: tuple[PositionSlot, ...]


def formation_positions(
    module: str,
    own_players: Sequence[Player],
) -> tuple[FormationPosition, ...]:
    """Le righe della formazione per il modulo, con posizioni Mantra vincolate.

    Per ogni riga (P, D, C, A) e per ogni posizione (ruolo richiesto dal
    template del modulo) assegna il primo giocatore proprio libero con quel
    ruolo esatto; le posizioni senza un giocatore disponibile restano con
    `player=None` (ruolo scoperto).

    Args:
        module: preset modulo (chiave di `MODULES`).
        own_players: giocatori presi dalla propria squadra, in ordine di
            presa.

    Returns:
        Una `FormationPosition` per gruppo, nell'ordine P, D, C, A.
    """
    template = MODULE_POSITIONS.get(module, MODULE_POSITIONS[DEFAULT_MODULE])
    unused = list(own_players)
    lines: list[FormationPosition] = []
    for group, role_names in zip(_LINE_GROUPS, template, strict=True):
        slots: list[PositionSlot] = []
        for role_name in role_names:
            role = Role(role_name)
            player = next((p for p in unused if role in player_roles(p)), None)
            if player is not None:
                unused.remove(player)
            slots.append(PositionSlot(role=role, player=player))
        lines.append(FormationPosition(group=group, positions=tuple(slots)))
    return tuple(lines)


def player_roles(player: Player) -> tuple[Role, ...]:
    """I ruoli del giocatore (multiruolo completo, fallback al primario)."""
    return player.roles or (player.role,)


def missing_roles(line: FormationPosition) -> tuple[str, ...]:
    """Ruoli Mantra scoperti di una riga della formazione (es. ("dd", "ds"))."""
    return tuple(slot.role.value for slot in line.positions if slot.player is None)


@dataclass(frozen=True)
class UtilityScore:
    """Punteggio di utilità con le tre componenti (0..1 ciascuna)."""

    score: float
    slot_need: float
    calendar_ease: float
    coverage: float


def team_strengths_from_players(players: Sequence[Player]) -> dict[str, float]:
    """Forza squadra stimata dal listone: media FVM per squadra (0..1).

    Usata come fallback pre-stagione quando non esistono risultati da cui
    derivare le medie reali.

    Args:
        players: tutti i giocatori del listone.

    Returns:
        team_id → media FVM dei suoi giocatori (solo squadre presenti).
    """
    totals: dict[str, tuple[float, int]] = {}
    for player in players:
        fvm = player.quote.fvm
        if fvm is None:
            continue
        prev = totals.get(player.team_id)
        totals[player.team_id] = (prev[0] + float(fvm), prev[1] + 1) if prev else (float(fvm), 1)
    return {team_id: total / count for team_id, (total, count) in totals.items()}


def utility_score(
    player: Player,
    league: LeagueContext,
    slots_left: Mapping[RoleGroup, int],
    own_players: Sequence[Player],
    module: str = DEFAULT_MODULE,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
) -> UtilityScore:
    """Utilità di acquisto del giocatore per la propria squadra (0..1).

    Media di tre componenti a peso uguale:
    - bisogno di ruolo dagli slot residui vs quota del modulo;
    - frazione delle giornate rimanenti con avversario facile (ignote = 0.5);
    - copertura aggiunta delle settimane facili rispetto a `own_players`.

    Args:
        player: giocatore da valutare (deve essere nel pool dei rimasti).
        league: contesto campionato (forze squadra, medie di lega).
        slots_left: slot di rosa residui per gruppo ruolo.
        own_players: giocatori già presi dalla propria squadra.
        module: preset modulo (chiave di `MODULES`).
        calendar: calendario rimanente per squadra (default: prossimi 5
            avversari di `league`, per compatibilità).
        team_strengths: forza squadra stimata (fallback pre-stagione).

    Returns:
        Punteggio complessivo e componenti, ciascuna in [0, 1].
    """
    outlook = opponent_outlook(player, league, calendar, team_strengths)
    slot_need = _slot_need(player, slots_left, module)
    calendar_ease = _ease_mean(outlook)
    coverage = _coverage(outlook, league, calendar, own_players, team_strengths)
    score = (slot_need + calendar_ease + coverage) / 3.0
    return UtilityScore(
        score=score,
        slot_need=slot_need,
        calendar_ease=calendar_ease,
        coverage=coverage,
    )


def opponent_outlook(
    player: Player,
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
) -> tuple[OpponentOutlook, ...]:
    """Gli avversari rimanenti con forza e flag "facile", in ordine di giornata.

    Un avversario è facile per attaccanti e centrocampisti quando la sua
    difesa (gol subiti a partita) è nel terzo inferiore delle squadre; per
    difensori e portieri quando il suo attacco (gol fatti) è nel terzo
    inferiore. A stagione non iniziata si usa `team_strengths` (proxy FVM);
    senza dati la forza è `None` e `easy` è `None`.

    Args:
        player: giocatore di cui si valuta il calendario.
        league: contesto campionato.
        calendar: calendario rimanente per squadra (default: prossimi 5
            avversari di `league`).
        team_strengths: forza squadra stimata (fallback pre-stagione).

    Returns:
        Una `OpponentOutlook` per giornata rimanente (vuota se mancano i dati).
    """
    team_calendar = calendar.get(player.team_id) if calendar else None
    context = league.teams.get(player.team_id)
    if team_calendar is not None:
        weeks = [(week.matchweek, week.opponent_id) for week in team_calendar.weeks]
    elif context is not None:
        weeks = [
            (league.current_matchweek + index + 1, opponent_id)
            for index, opponent_id in enumerate(context.upcoming_opponents)
        ]
    else:
        return ()
    if not weeks:
        return ()
    threshold = _easy_threshold(player, league, team_strengths)
    outlook: list[OpponentOutlook] = []
    for matchweek, opponent_id in weeks:
        opponent = league.teams.get(opponent_id)
        strength = _opponent_strength(player, opponent) if opponent else None
        if strength is None and team_strengths:
            strength = team_strengths.get(opponent_id)
        outlook.append(
            OpponentOutlook(
                team_name=opponent.team_name if opponent else opponent_id,
                matchweek=matchweek,
                strength=strength,
                easy=_is_easy(strength, threshold),
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


def easy_candidates(
    matchweek: int,
    players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
) -> tuple[Player, ...]:
    """Giocatori con avversario facile in una specifica giornata.

    Args:
        matchweek: giornata da valutare.
        players: giocatori da filtrare (es. i rimasti).
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).

    Returns:
        I giocatori con partita facile in quella giornata (ordine di input).
    """
    return tuple(
        player
        for player in players
        if any(
            opp.matchweek == matchweek and opp.easy is True
            for opp in opponent_outlook(player, league, calendar, team_strengths)
        )
    )


def week_coverage(
    own_players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
) -> tuple[WeekCoverage, ...]:
    """Copertura delle giornate rimanenti con i giocatori della propria squadra.

    Per ogni giornata rimanente: quanti giocatori propri giocano (presenti)
    e quanti affrontano un avversario facile per il loro ruolo.

    Args:
        own_players: giocatori già presi dalla propria squadra.
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).

    Returns:
        Una `WeekCoverage` per giornata rimanente, ordinate per matchweek.
    """
    outlooks = [opponent_outlook(own, league, calendar, team_strengths) for own in own_players]
    weeks = max((len(outlook) for outlook in outlooks), default=0)
    if weeks == 0:
        return ()
    matchweeks = [0] * weeks
    easy_counts = [0] * weeks
    present = [0] * weeks
    for outlook in outlooks:
        for week, opp in enumerate(outlook):
            matchweeks[week] = opp.matchweek
            present[week] += 1
            if opp.easy is True:
                easy_counts[week] += 1
    return tuple(
        WeekCoverage(
            matchweek=matchweeks[week],
            easy_count=easy_counts[week],
            present_count=present[week],
        )
        for week in range(weeks)
    )


def coverage_suggestions(
    own_players: Sequence[Player],
    remaining_players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
) -> tuple[WeekSuggestion, ...]:
    """Per ogni giornata scoperta, il miglior candidato rimasto che la copre.

    Una giornata è scoperta quando la propria squadra ha giocatori presenti
    ma nessuno con avversario facile. Per ogni giornata scoperta sceglie tra
    i rimasti con partita facile quello con più punti attesi.

    Args:
        own_players: giocatori già presi dalla propria squadra.
        remaining_players: giocatori ancora disponibili all'asta.
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).

    Returns:
        Una `WeekSuggestion` per giornata scoperta con candidati, in ordine
        di matchweek (le giornate senza candidati vengono saltate).
    """
    coverage = week_coverage(own_players, league, calendar, team_strengths)
    points = {player.url: project(player, league).total_points for player in remaining_players}
    suggestions: list[WeekSuggestion] = []
    for week in coverage:
        if not week.uncovered:
            continue
        candidates = easy_candidates(
            week.matchweek, remaining_players, league, calendar, team_strengths
        )
        best = max(candidates, key=lambda player: points.get(player.url, 0.0), default=None)
        if best is not None:
            suggestions.append(WeekSuggestion(week.matchweek, best, points[best.url]))
    return tuple(suggestions)


def coverage_recommendations(
    own_players: Sequence[Player],
    remaining_players: Sequence[Player],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None = None,
    team_strengths: Mapping[str, float] | None = None,
    limit: int = 3,
) -> tuple[CoverageRecommendation, ...]:
    """I rimasti che coprono più giornate scoperte (consiglio diretto).

    Le giornate target sono le scoperte della propria squadra; se non ce ne
    sono (rosa vuota o sempre coperta) il target sono tutte le giornate
    rimanenti, così il consiglio funziona anche pre-asta. Ranking: più
    giornate target coperte, poi punti attesi.

    Args:
        own_players: giocatori già presi dalla propria squadra.
        remaining_players: giocatori ancora disponibili all'asta.
        league: contesto campionato.
        calendar: calendario rimanente per squadra.
        team_strengths: forza squadra stimata (fallback pre-stagione).
        limit: numero massimo di consigli da restituire.

    Returns:
        Le `CoverageRecommendation` migliori (al massimo `limit`).
    """
    coverage = week_coverage(own_players, league, calendar, team_strengths)
    critical = [week.matchweek for week in coverage if week.uncovered]
    target = frozenset(critical) if critical else frozenset(remaining_weeks(league, calendar))
    points = {player.url: project(player, league).total_points for player in remaining_players}
    ranked: list[tuple[int, float, Player, tuple[int, ...]]] = []
    for player in remaining_players:
        outlook = opponent_outlook(player, league, calendar, team_strengths)
        covered = tuple(
            opp.matchweek for opp in outlook if opp.easy is True and opp.matchweek in target
        )
        if covered:
            ranked.append((len(covered), points.get(player.url, 0.0), player, covered))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return tuple(
        CoverageRecommendation(
            player=player,
            covered_weeks=covered,
            points=points.get(player.url, 0.0),
        )
        for _, _, player, covered in ranked[:limit]
    )


def remaining_weeks(
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None,
) -> tuple[int, ...]:
    """Le giornate rimanenti del campionato, in ordine.

    Derivate dal calendario rimanente (squadra con più giornate); senza
    calendario dai prossimi avversari di `league` (fallback di test).
    """
    if calendar:
        all_weeks = [team_calendar.weeks for team_calendar in calendar.values()]
        if all_weeks:
            longest = max(all_weeks, key=len)
            return tuple(week.matchweek for week in longest)
    if league.teams:
        lengths = [len(team.upcoming_opponents) for team in league.teams.values()]
        if lengths:
            return tuple(league.current_matchweek + 1 + index for index in range(max(lengths)))
    return ()


def _coverage(
    outlook: tuple[OpponentOutlook, ...],
    league: LeagueContext,
    calendar: Mapping[str, TeamCalendar] | None,
    own_players: Sequence[Player],
    team_strengths: Mapping[str, float] | None,
) -> float:
    """Copertura aggiunta nelle settimane facili del giocatore.

    Per ogni settimana facile del giocatore il guadagno è la quota di
    giocatori propri che quella settimana NON giocano già un avversario
    facile; media sulle settimane facili (0.5 neutro se nessuna).
    """
    coverage = week_coverage(own_players, league, calendar, team_strengths)
    gains = [
        1.0 - coverage[index].easy_count / coverage[index].present_count
        for index, opp in enumerate(outlook)
        if opp.easy is True and index < len(coverage) and coverage[index].present_count > 0
    ]
    if not gains:
        return 0.5
    return max(0.0, min(1.0, sum(gains) / len(gains)))


def _opponent_strength(player: Player, opponent) -> float | None:
    """Metrica di forza rilevante: attacco o difesa avversaria per ruolo."""
    if ROLE_GROUP[player.role] in (RoleGroup.A, RoleGroup.C):
        return opponent.ga_per_match
    return opponent.gf_per_match


def _easy_threshold(
    player: Player,
    league: LeagueContext,
    team_strengths: Mapping[str, float] | None,
) -> float | None:
    """Soglia "facile": terzo inferiore delle squadre per la metrica del ruolo.

    Con risultati reali si usano i gol subiti (attaccanti/centrocampisti) o
    fatti (difensori/portieri) delle squadre; pre-stagione il proxy FVM.
    Servono almeno 2 squadre con valore, altrimenti `None` (ignoto).

    Args:
        player: giocatore di cui si valuta il calendario.
        league: contesto campionato.
        team_strengths: forza squadra stimata (fallback pre-stagione).

    Returns:
        La forza alla soglia del terzo inferiore, oppure `None`.
    """
    attacking = ROLE_GROUP[player.role] in (RoleGroup.A, RoleGroup.C)
    if league.league_gf_per_match is not None:
        values = [
            team.ga_per_match if attacking else team.gf_per_match
            for team in league.teams.values()
            if (team.ga_per_match if attacking else team.gf_per_match) is not None
        ]
    elif team_strengths:
        values = [value for value in team_strengths.values() if value is not None]
    else:
        return None
    if len(values) < 2:
        return None
    ordered = sorted(values)
    return ordered[max(0, len(ordered) // 3 - 1)]


def _is_easy(strength: float | None, threshold: float | None) -> bool | None:
    """True se la forza è nel terzo inferiore; None se non confrontabile."""
    if strength is None or threshold is None:
        return None
    return strength <= threshold


def _ease_mean(outlook: tuple[OpponentOutlook, ...]) -> float:
    """Frazione di avversari facili; ignoti = 0.5; vuoto = 0.5."""
    if not outlook:
        return 0.5
    total = sum(1.0 if opp.easy is True else 0.0 if opp.easy is False else 0.5 for opp in outlook)
    return total / len(outlook)


_GROUP_INDEX: Mapping[RoleGroup, int] = {
    RoleGroup.P: 0,
    RoleGroup.D: 1,
    RoleGroup.C: 2,
    RoleGroup.A: 3,
}

_LINE_GROUPS = (RoleGroup.P, RoleGroup.D, RoleGroup.C, RoleGroup.A)
