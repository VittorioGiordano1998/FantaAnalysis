"""Guide asta: rose alternative per modulo, disegnate come formazioni.

Pagina M8-T6: calcola le k migliori rose per ogni modulo
(`guide.k_best_rosters`, cachato per snapshot asta + budget) e le mostra
come formazioni disegnate (stesso rendering della tab Asta); seconda tab
con il confronto tra moduli e alternative. Solo rendering e input: il
calcolo è delegato a `logic`.
"""

import pandas as pd
import streamlit as st

from guide import k_best_rosters
from state import spent_budget
from ui_common import (
    get_calendars,
    get_league,
    get_players,
    get_state,
    refresh_flag,
    render_formation,
)
from utility import (
    MODULES,
    formation_positions,
    player_roles,
    remaining_weeks,
    team_strengths_from_players,
)

ALTERNATIVES = 10


@st.cache_data(show_spinner=False)
def _rose(
    taken: tuple[tuple[str, str, int | None], ...],
    budget: int,
    force: bool,
) -> dict[str, tuple]:
    """Rose alternative per modulo (chiave = snapshot asta + budget)."""
    players = get_players(force)
    league = get_league(force)
    calendars = get_calendars(force)
    strengths = team_strengths_from_players(players)
    taken_set = frozenset(url for url, _, _ in taken)
    remaining = [p for p in players if p.url not in taken_set]
    return {
        module: k_best_rosters(
            module,
            remaining,
            league,
            calendars,
            strengths,
            budget=budget,
            k=ALTERNATIVES,
        )
        for module in MODULES
    }


def _render_rose() -> None:
    """Selettori modulo/alternativa + formazione disegnata + panchina."""
    state = get_state()
    taken = tuple((pick.player_url, pick.owner, pick.price) for pick in state.taken)
    budget = state.budget - spent_budget(state)
    force = refresh_flag()
    weeks = remaining_weeks(get_league(force), get_calendars(force))

    col_module, col_alt = st.columns(2)
    module = col_module.selectbox("Modulo", list(MODULES), key="guide_module")
    rose = _rose(taken, budget, force)[module]
    if not rose:
        st.warning(
            f"Con {budget} crediti la rosa non è realizzabile: aumenta il budget "
            "o libera crediti in tab Asta."
        )
        return
    labels = [f"Alternativa {index}" for index in range(1, len(rose) + 1)]
    alternative = col_alt.selectbox(
        "Alternativa", list(range(len(rose))), format_func=lambda i: labels[i], key="guide_alt"
    )
    squad = rose[alternative]
    st.caption(
        f"Costo {squad.total_cost} — coperto {len(squad.covered_weeks)}/{len(weeks)} "
        f"— punti {squad.total_points:.1f}"
    )
    render_formation(module, squad.selected)
    xi = [
        slot.player
        for line in formation_positions(module, squad.selected)
        for slot in line.positions
        if slot.player is not None
    ]
    bench = [player for player in squad.selected if player not in xi]
    with st.expander("Panchina"):
        if not bench:
            st.caption("Nessuna riserva.")
        else:
            frame = pd.DataFrame(
                [
                    {
                        "nome": player.name,
                        "squadra": player.team_name,
                        "ruolo": "/".join(role.value.upper() for role in player_roles(player)),
                        "qi": player.quote.qi,
                    }
                    for player in bench
                ]
            )
            st.dataframe(frame, hide_index=True, width="stretch")
    with st.expander("Giornate scoperte"):
        uncovered = tuple(w for w in weeks if w not in squad.covered_weeks)
        st.caption(", ".join(str(w) for w in uncovered) if uncovered else "Nessuna.")


def _render_confronto() -> None:
    """Tabella modulo × alternativa (costo, coperto, punti, scoperte)."""
    state = get_state()
    taken = tuple((pick.player_url, pick.owner, pick.price) for pick in state.taken)
    budget = state.budget - spent_budget(state)
    force = refresh_flag()
    weeks = remaining_weeks(get_league(force), get_calendars(force))
    rows = []
    for module, rose in _rose(taken, budget, force).items():
        for index, squad in enumerate(rose, start=1):
            rows.append(
                {
                    "modulo": module,
                    "alternativa": index,
                    "costo": squad.total_cost,
                    "coperto": f"{len(squad.covered_weeks)}/{len(weeks)}",
                    "punti": round(squad.total_points, 1),
                    "scoperte": ", ".join(str(w) for w in weeks if w not in squad.covered_weeks)
                    or "—",
                }
            )
    st.dataframe(
        pd.DataFrame(rows),
        column_config={
            "modulo": st.column_config.TextColumn("Modulo"),
            "alternativa": st.column_config.NumberColumn("Alternativa"),
            "costo": st.column_config.NumberColumn("Costo"),
            "coperto": st.column_config.TextColumn("Coperto"),
            "punti": st.column_config.NumberColumn("Punti"),
            "scoperte": st.column_config.TextColumn("Giornate scoperte"),
        },
        hide_index=True,
        width="stretch",
    )


def main() -> None:
    st.title("Guide asta")
    st.caption(
        "Rose alternative per modulo (10 per modulo), escludendo i top delle "
        "precedenti — aggiornate allo stato asta corrente."
    )
    players = get_players(refresh_flag())
    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return
    tab_rose, tab_confronto = st.tabs(["Rose alternative", "Confronto"])
    with tab_rose:
        _render_rose()
    with tab_confronto:
        _render_confronto()


if __name__ == "__main__":
    main()
