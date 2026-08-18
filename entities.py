"""Entità condivise del layer logic (ADR-0002).

`logic` è la shared truth: queste forme convergono sia sul percorso live
(scrape fresco) sia su quello cache (CSV). Nessun I/O qui.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum, StrEnum


class Role(StrEnum):
    """Ruolo Mantra come codificato da Fantacalcio.it (12 codici)."""

    POR = "por"
    DC = "dc"
    B = "b"
    DD = "dd"
    DS = "ds"
    E = "e"
    M = "m"
    C = "c"
    W = "w"
    T = "t"
    A = "a"
    PC = "pc"


class RoleGroup(Enum):
    """Gruppo di schieramento (rosa 2P-8D-8C-7A)."""

    P = "portiere"
    D = "difensore"
    C = "centrocampista"
    A = "attaccante"


ROLE_GROUP: Mapping[Role, RoleGroup] = {
    Role.POR: RoleGroup.P,
    Role.DC: RoleGroup.D,
    Role.B: RoleGroup.D,
    Role.DD: RoleGroup.D,
    Role.DS: RoleGroup.D,
    Role.E: RoleGroup.C,
    Role.M: RoleGroup.C,
    Role.C: RoleGroup.C,
    Role.W: RoleGroup.C,
    Role.T: RoleGroup.C,
    Role.A: RoleGroup.A,
    Role.PC: RoleGroup.A,
}

ROLE_LABELS: Mapping[Role, str] = {
    Role.POR: "Portiere",
    Role.DC: "Difensore centrale",
    Role.B: "Braccetto",
    Role.DD: "Difensore destro",
    Role.DS: "Difensore sinistro",
    Role.E: "Esterno",
    Role.M: "Mediano",
    Role.C: "Centrocampista centrale",
    Role.W: "Ala",
    Role.T: "Trequartista",
    Role.A: "Attaccante",
    Role.PC: "Punta centrale",
}

GROUP_LABELS: Mapping[RoleGroup, str] = {
    RoleGroup.P: "Portieri",
    RoleGroup.D: "Difensori",
    RoleGroup.C: "Centrocampisti",
    RoleGroup.A: "Attaccanti",
}


@dataclass(frozen=True)
class Quote:
    """Quotazioni di un giocatore (QI prezzo asta, QA aggiornata, FVM)."""

    qi: int | None
    qa: int | None = None
    fvm: int | None = None


@dataclass(frozen=True)
class SeasonStats:
    """Statistiche stagionali (Fantacalcio.it, pagina statistiche)."""

    played_matches: int | None = None
    grade_avg: float | None = None
    fanta_avg: float | None = None
    goals: int | None = None
    goals_against: int | None = None
    penalties_scored: int | None = None
    penalties_total: int | None = None
    penalties_saved: int | None = None
    assists: int | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None


@dataclass(frozen=True)
class Player:
    """Giocatore del listone con quotazione e (opzionali) stats stagionali.

    `role` è il ruolo primario (primo del pill Mantra); `roles` è il
    multiruolo completo (vuoto = solo `role`), vedi ADR-0005.
    """

    name: str
    role: Role
    team_id: str
    team_code: str
    team_name: str
    quote: Quote
    url: str
    stats: SeasonStats | None = None
    roles: tuple[Role, ...] = ()


@dataclass(frozen=True)
class TakenPick:
    """Giocatore preso all'asta: da chi e (per la propria squadra) a che prezzo."""

    player_url: str
    owner: str
    price: int | None = None


@dataclass(frozen=True)
class ListoneRow:
    """Riga del listone completo (file Excel dell'utente, display-only).

    Contiene tutte le informazioni del listone: ruoli Mantra nell'ordine
    del file, squadra, titolarità (%), FMV, specialità con priorità
    (rigorista, punizioni, angoli: 1 = primo tiratore/battitore, 2 =
    secondo, ...) e stato all'asta (preso dalla propria squadra / da
    altri). Non partecipa alle proiezioni né all'ottimizzazione.
    """

    name: str
    team_name: str
    roles: tuple[Role, ...]
    titolarita: float | None
    fmv: float | None
    rigorista: int | None
    punizioni: int | None
    angoli: int | None
    preso_noi: bool
    preso_altri: bool


@dataclass(frozen=True)
class ListoneState:
    """Stato delle prese segnate dal listone: budget e prezzi pagati.

    `flags` mappa nome giocatore → "noi" | "altri" | "" (libero esplicito);
    `prices` mappa nome giocatore → crediti pagati (solo presi da noi).
    """

    budget: int
    flags: dict[str, str] = dataclasses.field(default_factory=dict)
    prices: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclass(frozen=True)
class AuctionState:
    """Stato dell'asta (ADR-0004): budget totale, squadra propria, prese."""

    budget: int
    own_team: str = "Io"
    taken: tuple[TakenPick, ...] = ()


def attach_stats(
    players: Iterable[Player],
    stats_by_url: Mapping[str, SeasonStats],
) -> list[Player]:
    """Arricchisce i giocatori con le stats stagionali (per `url`).

    Args:
        players: giocatori da arricchire.
        stats_by_url: stats chiavate sull'URL della pagina giocatore.

    Returns:
        Nuovi `Player` con `stats` impostate (o `None` se assenti).
    """
    return [dataclasses.replace(player, stats=stats_by_url.get(player.url)) for player in players]
