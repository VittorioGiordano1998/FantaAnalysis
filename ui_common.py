"""Helper condivisi tra main.py e le pagine Streamlit (layer ui).

Solo rendering/input e accesso allo stato di sessione: rete, cache CSV e
JSON restano nei moduli data; il calcolo in logic.
"""

from __future__ import annotations

import streamlit as st

from entities import AuctionState, Player, RoleGroup, attach_stats
from fetch_fixtures import read_league_context
from fetch_quotazioni import read_players
from fetch_stats import read_season_stats
from projection import LeagueContext
from state import load_state, save_state, slots_remaining, spent_budget

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
