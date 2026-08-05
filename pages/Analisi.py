"""Analisi dei giocatori rimasti: proiezioni, qualità/prezzo, calendario.

Pagina M5-T4: tabelle compatte (mobile) con proiezioni punti per ruolo,
rapporto qualità/prezzo e prossimi 5 avversari con la forza squadra.
Tutto deriva da `logic` (projection) e dai cache data.
"""

import pandas as pd
import streamlit as st

from entities import GROUP_LABELS, ROLE_GROUP, ROLE_LABELS
from projection import project
from state import taken_urls
from ui_common import get_league, get_players, get_state, refresh_flag


def _analisi_frame(players, league) -> pd.DataFrame:
    rows = []
    for player in players:
        proj = project(player, league)
        qi = player.quote.qi or 0
        rows.append(
            {
                "name": player.name,
                "team": player.team_name,
                "role": ROLE_LABELS[player.role],
                "group": GROUP_LABELS[ROLE_GROUP[player.role]],
                "qi": qi,
                "ppm": proj.points_per_match,
                "points": proj.total_points,
                "qp": proj.total_points / qi if qi else 0.0,
            }
        )
    return pd.DataFrame(rows)


def _render_analisi(players, league) -> None:
    st.subheader("Giocatori rimasti")
    taken = taken_urls(get_state())
    remaining = [p for p in players if p.url not in taken]
    frame = _analisi_frame(remaining, league)

    group_filter = st.selectbox(
        "Gruppo ruolo", ["Tutti", *GROUP_LABELS.values()], key="analisi_group"
    )
    team_filter = st.selectbox(
        "Squadra",
        ["Tutte", *sorted({row["team"] for _, row in frame.iterrows()})],
        key="analisi_team",
    )
    filtered = frame
    if group_filter != "Tutti":
        filtered = filtered[filtered["group"] == group_filter]
    if team_filter != "Tutte":
        filtered = filtered[filtered["team"] == team_filter]
    filtered = filtered.sort_values("qp", ascending=False)

    st.dataframe(
        filtered,
        column_config={
            "name": st.column_config.TextColumn("Nome"),
            "team": st.column_config.TextColumn("Squadra"),
            "role": st.column_config.TextColumn("Ruolo"),
            "qi": st.column_config.NumberColumn("QI"),
            "ppm": st.column_config.NumberColumn("Punti/partita", format="%.2f"),
            "points": st.column_config.NumberColumn("Punti stagione", format="%.1f"),
            "qp": st.column_config.NumberColumn("Qualità/prezzo", format="%.2f"),
        },
        hide_index=True,
        width="stretch",
    )
    st.caption(f"{len(filtered)} giocatori — ordinati per qualità/prezzo (punti/QI)")


def _render_calendario(players, league) -> None:
    st.subheader("Calendario prossime 5 giornate")
    if not league.teams:
        st.info("Nessun dato calendario: esegui 'Aggiorna dati'.")
        return
    team_names = sorted({player.team_name for player in players})
    team_filter = st.selectbox("Squadra", team_names, key="calendario_team")
    team = next(
        (t for t in league.teams.values() if t.team_name == team_filter),
        None,
    )
    if team is None or not team.upcoming_opponents:
        st.info("Nessuna partita futura disponibile.")
        return
    rows = []
    for opponent_id in team.upcoming_opponents:
        opponent = league.teams.get(opponent_id)
        if opponent is None:
            continue
        rows.append(
            {
                "avversario": opponent.team_name,
                "gol_fatti": _fmt_strength(opponent.gf_per_match),
                "gol_subiti": _fmt_strength(opponent.ga_per_match),
            }
        )
    st.dataframe(
        pd.DataFrame(rows),
        column_config={
            "avversario": st.column_config.TextColumn("Avversario"),
            "gol_fatti": st.column_config.TextColumn("Gol fatti/partita"),
            "gol_subiti": st.column_config.TextColumn("Gol subiti/partita"),
        },
        hide_index=True,
        width="stretch",
    )
    gf = league.league_gf_per_match
    if gf is not None:
        st.caption(f"Media di lega: {gf:.2f} gol a partita")


def _fmt_strength(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "—"


def main() -> None:
    st.title("Analisi")
    force = refresh_flag()
    players = get_players(force)
    league = get_league(force)
    _render_analisi(players, league)
    _render_calendario(players, league)


if __name__ == "__main__":
    main()
