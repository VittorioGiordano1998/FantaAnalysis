"""Proiezioni punti per ruolo Mantra (layer logic, ADR-0002).

Pura computazione, nessun I/O: i dati arrivano come tipi condivisi
(`Player`, `LeagueContext`). Il modello degrada con eleganza: senza stats
stagionali (o a stagione non iniziata) stima dai punti medi impliciti
nell'FVM; l'aggiustamento calendario è neutro finché non esistono risultati.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from entities import ROLE_GROUP, Player, RoleGroup

SEASON_MATCHWEEKS = 38
NEXT_WEEKS = 5
MIN_MATCHES_FOR_STATS = 3
FVM_PPM_DIVISOR = 100.0
CALENDAR_ALPHA = 0.5
CALENDAR_CAP = 0.10


@dataclass(frozen=True)
class TeamContext:
    """Forza e calendario di una squadra (dai risultati già giocati)."""

    team_id: str
    team_name: str
    gf_per_match: float | None
    ga_per_match: float | None
    upcoming_opponents: tuple[str, ...]


@dataclass(frozen=True)
class LeagueContext:
    """Contesto campionato per le proiezioni (ADR-0002)."""

    season: str
    current_matchweek: int
    teams: Mapping[str, TeamContext]
    league_gf_per_match: float | None = None
    league_ga_per_match: float | None = None


@dataclass(frozen=True)
class PlayerProjection:
    """Proiezione punti di un giocatore sul resto della stagione."""

    points_per_match: float
    matches_expected: float
    calendar_multiplier: float
    total_points: float


def points_per_match(player: Player) -> float:
    """Punti fanta attesi a partita (ADR-0002).

    Con almeno `MIN_MATCHES_FOR_STATS` partite a voto si usa la fantamedia
    (include bonus/malus); con 1-2 partite si fa una media con la stima FVM;
    senza stats (o stagione non iniziata) si stima da `fvm / 100`.

    Args:
        player: giocatore con quotazione e (opzionali) stats.

    Returns:
        Punti fanta attesi a partita.
    """
    fvm_ppm = _fvm_points_per_match(player)
    stats = player.stats
    if stats is None:
        return fvm_ppm
    played = stats.played_matches or 0
    if played >= MIN_MATCHES_FOR_STATS:
        return stats.fanta_avg if stats.fanta_avg is not None else fvm_ppm
    if played > 0 and stats.fanta_avg is not None:
        return (stats.fanta_avg + fvm_ppm) / 2
    return fvm_ppm


def playing_share(player: Player, league: LeagueContext) -> float:
    """Frazione di giornate in cui il giocatore è atteso in campo.

    I minuti giocati non sono esposti dalla fonte (KI-1): si usa la quota di
    giornate della squadra già giocate coperte da partite a voto del
    giocatore; a stagione non iniziata (o senza stats) la stima è 1.0.

    Args:
        player: giocatore con (opzionali) stats.
        league: contesto campionato (per le giornate giocate).

    Returns:
        Frazione in [0, 1].
    """
    stats = player.stats
    if stats is None or not stats.played_matches:
        return 1.0
    rounds_played = league.current_matchweek - 1
    if rounds_played <= 0:
        return 1.0
    return min(1.0, stats.played_matches / rounds_played)


def expected_remaining_matches(player: Player, league: LeagueContext) -> float:
    """Partite attese del giocatore sul resto della stagione.

    Args:
        player: giocatore.
        league: contesto campionato.

    Returns:
        Numero atteso di partite dal resto della stagione.
    """
    remaining = max(0, SEASON_MATCHWEEKS - (league.current_matchweek - 1))
    return playing_share(player, league) * remaining


def calendar_multiplier(player: Player, league: LeagueContext) -> float:
    """Moltiplicatore di forza avversari sulle prossime 5 giornate.

    Per attaccanti e centrocampisti il moltiplicatore cresce con la
    debolezza della difesa avversaria (media gol subiti); per difensori e
    portieri con la debolezza dell'attacco avversario (media gol fatti).
    Senza risultati giocati (o squadra/avversari senza dati) è neutro (1.0);
    il risultato è clampato a `[1 - CALENDAR_CAP, 1 + CALENDAR_CAP]`.

    Args:
        player: giocatore di cui si valuta il calendario.
        league: contesto campionato (forze squadra + prossimi avversari).

    Returns:
        Moltiplicatore in [0.9, 1.1] (neutro se mancano i dati).
    """
    context = league.teams.get(player.team_id)
    if context is None or not context.upcoming_opponents:
        return 1.0
    opponents = [league.teams[oid] for oid in context.upcoming_opponents if oid in league.teams]
    if not opponents:
        return 1.0
    if ROLE_GROUP[player.role] in (RoleGroup.A, RoleGroup.C):
        return _opponent_multiplier(opponents, league.league_ga_per_match, attacking=True)
    return _opponent_multiplier(opponents, league.league_gf_per_match, attacking=False)


def project(player: Player, league: LeagueContext) -> PlayerProjection:
    """Proiezione completa del giocatore (ADR-0002).

    Il moltiplicatore calendario si applica solo alle prossime `NEXT_WEEKS`
    giornate; le restanti partite contano a moltiplicatore neutro.

    Args:
        player: giocatore da proiettare.
        league: contesto campionato.

    Returns:
        Proiezione punti totali sul resto della stagione.
    """
    ppm = points_per_match(player)
    matches = expected_remaining_matches(player, league)
    multiplier = calendar_multiplier(player, league)
    adjusted_weeks = min(NEXT_WEEKS, matches)
    rest = max(0.0, matches - NEXT_WEEKS)
    total = ppm * (multiplier * adjusted_weeks + rest)
    return PlayerProjection(
        points_per_match=ppm,
        matches_expected=matches,
        calendar_multiplier=multiplier,
        total_points=total,
    )


def _fvm_points_per_match(player: Player) -> float:
    """Stima punti/partita dall'FVM (esposto già diviso per 1000)."""
    fvm = player.quote.fvm or 0
    return fvm / FVM_PPM_DIVISOR


def _opponent_multiplier(
    opponents: list[TeamContext],
    league_avg: float | None,
    *,
    attacking: bool,
) -> float:
    """Moltiplicatore dalla media avversaria (attacco o difesa, ADR-0002)."""
    values = [opp.gf_per_match if not attacking else opp.ga_per_match for opp in opponents]
    values = [v for v in values if v is not None]
    if not values or league_avg is None or league_avg <= 0:
        return 1.0
    mean = sum(values) / len(values)
    ratio = (mean - league_avg) / league_avg
    multiplier = 1 + CALENDAR_ALPHA * ratio if attacking else 1 - CALENDAR_ALPHA * ratio
    return min(1 + CALENDAR_CAP, max(1 - CALENDAR_CAP, multiplier))
