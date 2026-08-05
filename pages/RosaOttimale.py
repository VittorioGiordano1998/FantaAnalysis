"""Rosa ottimale tra i rimasti e limite di spesa per il giocatore in asta.

Pagina M5-T3: la rosa riflette lo stato asta corrente (prese, budget
residuo, slot residui) e il limite di spesa si calcola on-demand per il
giocatore selezionato (~2-3 s, cachato per snapshot). Solo rendering e
input; il calcolo Ã¨ delegato a `optimize`/`projection`.
"""

import pandas as pd
import streamlit as st

from entities import ROLE_LABELS, RoleGroup
from optimize import SpendingLimit, SquadResult, optimize_squad, spending_limit
from projection import LeagueContext, project
from ui_common import get_league, get_players, refresh_flag, slot_tuple, state_snapshot

GROUP_SHORT = {
    RoleGroup.P: "P",
    RoleGroup.D: "D",
    RoleGroup.C: "C",
    RoleGroup.A: "A",
}


@st.cache_data(show_spinner=False)
def _solve_rosa(
    taken: tuple[tuple[str, str, int | None], ...],
    budget: int,
    slots: tuple[tuple[str, int], ...],
    force: bool,
) -> SquadResult:
    """Rosa ottimale con budget e slot residui (chiave = snapshot input)."""
    players = get_players(force)
    league = get_league(force)
    return optimize_squad(
        players,
        league,
        budget=budget,
        slots={RoleGroup(name): count for name, count in slots},
        taken_urls=frozenset(url for url, _, _ in taken),
    )


@st.cache_data(show_spinner=False)
def _limit_for(
    player_url: str,
    taken: tuple[tuple[str, str, int | None], ...],
    budget: int,
    slots: tuple[tuple[str, int], ...],
    force: bool,
) -> SpendingLimit:
    """Limite di spesa per un giocatore (chiave = snapshot input)."""
    players = get_players(force)
    league = get_league(force)
    player = next(p for p in players if p.url == player_url)
    return spending_limit(
        player,
        players,
        league,
        budget=budget,
        slots={RoleGroup(name): count for name, count in slots},
        taken_urls=frozenset(url for url, _, _ in taken),
    )


def _state_inputs():
    """Snapshot dello stato asta per le chiavi cache."""
    return state_snapshot()


def _render_rosa(taken, budget, slots, players, force) -> LeagueContext:
    st.subheader("Rosa ottimale")
    st.caption(
        "Budget residuo "
        + f"{budget} — slot: "
        + " ".join(f"{GROUP_SHORT[g]} {n}" for g, n in slots.items())
    )
    result = _solve_rosa(taken, budget, slot_tuple(slots), force)
    if result.status != "Optimal":
        st.warning("Rosa non realizzabile: pool o budget insufficiente.")
        return None
    league = get_league(force)
    frame = pd.DataFrame(
        [
            {
                "name": player.name,
                "team": player.team_name,
                "role": ROLE_LABELS[player.role],
                "price": player.quote.qi or 0,
                "points": project(player, league).total_points,
            }
            for player in result.selected
        ]
    )
    st.dataframe(
        frame,
        column_config={
            "name": st.column_config.TextColumn("Nome"),
            "team": st.column_config.TextColumn("Squadra"),
            "role": st.column_config.TextColumn("Ruolo"),
            "price": st.column_config.NumberColumn("Prezzo"),
            "points": st.column_config.NumberColumn("Punti attesi", format="%.1f"),
        },
        hide_index=True,
        width="stretch",
    )
    st.caption(
        f"Punti attesi totali: {result.total_points:.1f} — costo {result.total_cost}"
        f" / {budget} crediti"
    )
    return league


def _render_limite(taken, budget, slots, players, force) -> None:
    st.subheader("Limite di spesa")
    by_label = {
        f"{player.name} — {player.team_name}": player.url
        for player in players
        if player.url not in frozenset(url for url, _, _ in taken)
    }
    if not by_label:
        st.info("Nessun giocatore disponibile.")
        return
    label = st.selectbox("Giocatore in asta", list(by_label), key="limit_player")
    if st.button("Calcola limite", key="limit_run", type="primary"):
        with st.spinner("Calcolo in corso (pochi secondi)..."):
            limit = _limit_for(by_label[label], taken, budget, slot_tuple(slots), force)
        if limit.status != "Optimal":
            st.warning("Rosa di base non realizzabile: nessun limite calcolabile.")
            return
        player_name = label.rsplit(" — ", 1)[0]
        st.success(f"Offri al massimo {limit.max_price} crediti per {player_name}.")
        st.caption(
            f"Senza di lui la rosa vale {limit.baseline_points:.1f} punti; con lui "
            f"a {limit.max_price} crediti resta {limit.forced_points:.1f} punti."
        )


def main() -> None:
    st.title("Rosa ottimale")
    force = refresh_flag()
    taken, budget, slots, players = _state_inputs()
    _render_rosa(taken, budget, slots, players, force)
    _render_limite(taken, budget, slots, players, force)


if __name__ == "__main__":
    main()
