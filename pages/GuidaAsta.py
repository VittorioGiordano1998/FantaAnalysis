"""Guida asta per squadra: rosa completa ordinata per ruolo (come FantaLab).

Pagina M8-T9: selettore squadra e, per la squadra scelta, la rosa completa
raggruppata per gruppo ruolo con QI/QA/FVM, media voto, presenze e stato
(libero o preso all'asta). Solo rendering e input: i dati arrivano dalle
cache data via `ui_common` (quotazioni + stats) e dallo stato asta.
"""

import pandas as pd
import streamlit as st

from entities import GROUP_LABELS, ROLE_GROUP, Role, RoleGroup
from ui_common import get_players, get_state, refresh_flag, role_codes
from utility import player_roles

ROLE_ORDER = (
    Role.POR,
    Role.DC,
    Role.B,
    Role.DD,
    Role.DS,
    Role.E,
    Role.M,
    Role.C,
    Role.W,
    Role.T,
    Role.A,
    Role.PC,
)


def _role_key(player) -> int:
    """Posizione del ruolo primario nell'ordine listone (come la guida FantaLab)."""
    return ROLE_ORDER.index(player.role) if player.role in ROLE_ORDER else len(ROLE_ORDER)


def _team_players(players, team_name: str, group: RoleGroup) -> list:
    """Rosa della squadra per gruppo, ordinata per ruolo → QI → nome."""
    return sorted(
        (
            player
            for player in players
            if player.team_name == team_name and ROLE_GROUP[player.role] is group
        ),
        key=lambda player: (_role_key(player), -(player.quote.qi or 0), player.name.lower()),
    )


def _group_frame(players: list, owners: dict[str, str]) -> pd.DataFrame:
    """Frame compatto della rosa di un gruppo ruolo (con stato asta)."""
    rows = []
    for player in players:
        stats = player.stats
        owner = owners.get(player.url)
        rows.append(
            {
                "nome": player.name,
                "ruoli": role_codes(player_roles(player)),
                "qi": player.quote.qi,
                "qa": player.quote.qa,
                "fvm": player.quote.fvm,
                "media": stats.grade_avg if stats else None,
                "presenze": stats.played_matches if stats else None,
                "stato": f"Preso — {owner}" if owner else "Libero",
            }
        )
    return pd.DataFrame(rows)


def _render_guida(players, state) -> None:
    """Selettore squadra + rosa per gruppo ruolo con QI/QA/FVM e stato."""
    teams = sorted({player.team_name for player in players})
    team = st.selectbox("Squadra", teams, key="guida_team")
    owners = {pick.player_url: pick.owner for pick in state.taken if pick.player_url}
    st.subheader(team)
    total_qi = sum(player.quote.qi or 0 for player in players if player.team_name == team)
    st.caption(
        f"{sum(1 for player in players if player.team_name == team)} giocatori "
        f"— QI totale {total_qi} crediti"
    )
    for group in RoleGroup:
        roster = _team_players(players, team, group)
        if not roster:
            continue
        st.markdown(f"#### {GROUP_LABELS[group]}")
        st.dataframe(
            _group_frame(roster, owners),
            column_config={
                "nome": st.column_config.TextColumn("Nome"),
                "ruoli": st.column_config.TextColumn("Ruolo"),
                "qi": st.column_config.NumberColumn("QI"),
                "qa": st.column_config.NumberColumn("QA"),
                "fvm": st.column_config.NumberColumn("FVM"),
                "media": st.column_config.NumberColumn("Media", format="%.2f"),
                "presenze": st.column_config.NumberColumn("Presenze"),
                "stato": st.column_config.TextColumn("Stato"),
            },
            hide_index=True,
            width="stretch",
        )
        st.caption(f"{len(roster)} giocatori — QI {sum(player.quote.qi or 0 for player in roster)}")


def main() -> None:
    st.title("Guida asta")
    st.caption(
        "Rosa completa per squadra, ordinata per ruolo (come la Guida Asta "
        "di FantaLab) con QI/QA/FVM, media voto, presenze e stato all'asta."
    )
    players = get_players(refresh_flag())
    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return
    state = get_state()
    _render_guida(players, state)


if __name__ == "__main__":
    main()
