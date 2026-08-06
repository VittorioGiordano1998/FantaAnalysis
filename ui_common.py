"""Helper condivisi tra main.py e le pagine Streamlit (layer ui).

Solo rendering/input e accesso allo stato di sessione: rete, cache CSV e
JSON restano nei moduli data; il calcolo in logic.
"""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from entities import GROUP_LABELS, ROLE_LABELS, AuctionState, Player, Role, RoleGroup, attach_stats
from fetch_fixtures import read_league_context, read_remaining_calendar
from fetch_quotazioni import read_players
from fetch_stats import read_season_stats
from projection import LeagueContext
from state import load_state, save_state, slots_remaining, spent_budget
from utility import TeamCalendar, formation_positions, missing_roles, player_roles

STATE_KEY = "asta"
REFRESH_KEY = "aggiorna_dati"


@st.cache_data(show_spinner=False)
def get_players(force: bool) -> list[Player]:
    """Giocatori del listone con stats, chiave = flag aggiornamento."""
    return attach_stats(read_players(), read_season_stats())


@st.cache_data(show_spinner=False)
def get_league(force: bool) -> LeagueContext:
    """Contesto campionato per le proiezioni, chiave = flag aggiornamento."""
    return read_league_context()


@st.cache_data(show_spinner=False)
def get_calendars(force: bool) -> dict[str, TeamCalendar]:
    """Calendario rimanente per squadra, chiave = flag aggiornamento."""
    return read_remaining_calendar()


def refresh_flag() -> bool:
    """True se l'utente ha richiesto un aggiornamento dati (invalida cache)."""
    return bool(st.session_state.get(REFRESH_KEY, False))


def get_state() -> AuctionState:
    """Stato asta di sessione (creato dal file locale se assente)."""
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = load_state()
    return st.session_state[STATE_KEY]


def set_state(state: AuctionState) -> None:
    """Aggiorna lo stato di sessione e lo persiste localmente (convenienza)."""
    st.session_state[STATE_KEY] = state
    save_state(state)


def state_snapshot(
    budget: int | None = None,
) -> tuple[tuple[tuple[str, str, int | None], ...], int, dict[RoleGroup, int], list[Player]]:
    """Snapshot dello stato asta per le chiavi cache dei calcoli pesanti.

    Returns:
        (prese, budget residuo, slot residui, giocatori con stats).
    """
    state = get_state()
    players = get_players(refresh_flag())
    slots = slots_remaining(state, players)
    remaining = budget if budget is not None else state.budget - spent_budget(state)
    taken = tuple((pick.player_url, pick.owner, pick.price) for pick in state.taken)
    return taken, remaining, slots, players


def slot_tuple(slots: dict[RoleGroup, int]) -> tuple[tuple[str, int], ...]:
    """Slot come tupla ordinata (hashabile) per le chiavi cache."""
    return tuple(sorted((group.value, count) for group, count in slots.items()))


def role_codes(roles: tuple[Role, ...]) -> str:
    """Codici ruolo compatti come sul listone (es. "E/W")."""
    return "/".join(role.value.upper() for role in roles)


def render_formation(module: str, players: Sequence[Player]) -> None:
    """Disegna la formazione del modulo con i giocatori dati (XI o rosa).

    Una riga per gruppo ruolo con le posizioni del template: nei posti
    occupati nome, squadra e codici multiruolo del giocatore; nei posti
    scoperti "—" con il ruolo richiesto e la riga "Mancano: ...".
    """
    for line in formation_positions(module, players):
        st.caption(GROUP_LABELS[line.group])
        cols = st.columns(len(line.positions))
        for index, col in enumerate(cols):
            slot = line.positions[index]
            with col.container(border=True):
                if slot.player is not None:
                    st.markdown(f"**{slot.player.name}**")
                    st.caption(slot.player.team_name)
                    st.caption(role_codes(player_roles(slot.player)))
                else:
                    st.markdown("—")
                    st.caption(ROLE_LABELS[slot.role])
        missing = missing_roles(line)
        if missing:
            st.caption("Mancano: " + ", ".join(ROLE_LABELS[Role(role)] for role in missing))
