"""FantaOptimizer — schermata unica: copertura delle partite facili.

Si cerca un calciatore e l'app dice quali altri prendere per coprire le
giornate con partita facile (M8-T8). Solo rendering e input: la logica di
rete/cache è delegata ai moduli data, il calcolo a `logic`
(entities/projection/utility/guide), lo stato a `state.py`.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from entities import RoleGroup
from export_excel import build_report
from fetch_fixtures import get_calendario
from fetch_quotazioni import get_quotazioni
from fetch_stats import get_statistiche
from guide import GreedyPick, coverage_completion
from optimize import optimize_squad
from projection import project
from state import export_state, import_state
from utility import (
    opponent_outlook,
    player_roles,
    remaining_weeks,
    team_strengths_from_players,
)

logger = logging.getLogger(__name__)

try:
    from ui_common import (  # noqa: F401
        get_calendars,
        get_league,
        get_players,
        get_state,
        refresh_flag,
        set_state,
        slot_tuple,
        state_snapshot,
    )
except ImportError as exc:
    logger.exception("Deploy incompleto: import falliti al boot (%s)", exc)
    st.error(
        "Deploy incompleto: il server sta servendo file di versioni diverse. "
        "Chiudi l'app, eliminala e ricreala su Streamlit Cloud (Delete app → "
        "Create app dallo stesso repository), poi riapri — la versione corretta "
        "è mostrata nella sidebar."
    )
    st.stop()

st.set_page_config(page_title="FantaOptimizer", layout="wide")


@st.cache_data(show_spinner=False)
def _build_report_bytes(
    taken: tuple[tuple[str, str, int | None], ...],
    budget: int,
    slots: tuple[tuple[str, int], ...],
    force: bool,
) -> bytes:
    """Report Excel completo (M6-T1), chiave = snapshot input.

    Returns:
        Bytes del report, oppure b"" se la rosa non è realizzabile.
    """
    players = get_players(force)
    league = get_league(force)
    taken_set = frozenset(url for url, _, _ in taken)
    squad = optimize_squad(
        players,
        league,
        budget=budget,
        slots={RoleGroup(name): count for name, count in slots},
        taken_urls=taken_set,
    )
    if squad.status != "Optimal":
        return b""
    return build_report(squad, players, league, taken_set)


@st.cache_data(show_spinner=False)
def _completion(
    player_url: str,
    taken: tuple[tuple[str, str, int | None], ...],
    force: bool,
) -> tuple[tuple[int, ...], tuple[GreedyPick, ...], tuple[int, ...]]:
    """Copertura per il giocatore cercato (chiave = giocatore + prese).

    Returns:
        (giornate facili del cercato, suggerimenti di presa, tutte le
        giornate rimanenti).
    """
    players = get_players(force)
    league = get_league(force)
    calendars = get_calendars(force)
    strengths = team_strengths_from_players(players)
    taken_set = frozenset(url for url, _, _ in taken)
    remaining = [player for player in players if player.url not in taken_set]
    player = next(player for player in remaining if player.url == player_url)
    own_weeks = tuple(
        opp.matchweek
        for opp in opponent_outlook(player, league, calendars, strengths)
        if opp.easy is True
    )
    picks = coverage_completion(player, remaining, league, calendars, strengths)
    return own_weeks, picks, remaining_weeks(league, calendars)


def _app_version() -> str:
    """Versione deployata (da version.txt), per la diagnosi."""
    try:
        return Path("version.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return "?"


def _render_sidebar() -> None:
    """Azioni di sistema: aggiorna dati, stato asta, report."""
    with st.sidebar:
        st.caption(f"Versione: {_app_version()}")
        st.subheader("Dati")
        _render_aggiorna_dati()
        _render_export_import()
        _render_report()


def _render_aggiorna_dati() -> None:
    """Pulsante "Aggiorna dati": unica via di invalidazione delle cache."""
    if st.button("Aggiorna dati"):
        with st.spinner("Aggiornamento dati in corso..."):
            get_quotazioni(force_refresh=True)
            get_statistiche(force_refresh=True)
            get_calendario(force_refresh=True)
        st.session_state.aggiorna_dati = not st.session_state.aggiorna_dati
        st.rerun()


def _render_export_import() -> None:
    """Export/import dello stato asta via bytes (percorso ufficiale Cloud)."""
    with st.sidebar:
        st.subheader("Stato asta")
        st.download_button(
            "Esporta stato",
            data=export_state(get_state()),
            file_name="asta.json",
            mime="application/json",
        )
        uploaded = st.file_uploader("Importa stato", type="json")
        if uploaded is not None:
            try:
                imported = import_state(uploaded.getvalue())
            except ValueError:
                st.error("File di stato non valido.")
            else:
                set_state(imported)
                st.rerun()


def _render_report() -> None:
    """Report Excel completo (M6-T1) nella sidebar."""
    with st.sidebar:
        st.subheader("Report")
        taken, budget, slots, players = state_snapshot()
        if not players:
            st.info("Dati non ancora scaricati: esegui 'Aggiorna dati'.")
            return
        data = _build_report_bytes(taken, budget, slot_tuple(slots), refresh_flag())
        if not data:
            st.info("Rosa non realizzabile: report non disponibile.")
        else:
            st.download_button(
                "Scarica report Excel",
                data=data,
                file_name="report_fanta.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


def _render_copertura_giocatore() -> None:
    """Cerca un calciatore: chi prendere per coprire le partite facili."""
    st.subheader("Copertura partite facili")
    state = get_state()
    players = get_players(refresh_flag())
    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return
    taken = frozenset(pick.player_url for pick in state.taken)
    by_label = {
        f"{player.name} — {player.team_name}": player.url
        for player in players
        if player.url not in taken
    }
    if not by_label:
        st.info("Tutti i giocatori del listone sono già presi.")
        return
    label = st.selectbox("Calciatore", list(by_label), key="cover_player")
    with st.spinner("Calcolo copertura in corso..."):
        taken_tuple = tuple((pick.player_url, pick.owner, pick.price) for pick in state.taken)
        own_weeks, picks, weeks = _completion(by_label[label], taken_tuple, refresh_flag())
    player_name = label.rsplit(" — ", 1)[0]
    total = len(weeks)
    st.caption(
        f"Partite facili di {player_name}: "
        + (", ".join(str(week) for week in own_weeks) if own_weeks else "nessuna")
    )
    if not picks:
        if len(set(own_weeks)) == total:
            st.success(f"Con {player_name} copri già tutte le {total} giornate facili.")
        else:
            st.info(
                "Nessun altro giocatore aggiunge giornate facili oltre a quelle "
                f"già coperte ({len(set(own_weeks))}/{total})."
            )
        return
    final_covered = len(picks[-1].covered_weeks)
    st.success(
        f"Con {player_name} copri {len(set(own_weeks))}/{total} giornate facili: "
        f"prendendo questi arrivi a {final_covered}/{total}."
    )
    league = get_league(refresh_flag())
    frame = pd.DataFrame(
        [
            {
                "nome": pick.player.name,
                "squadra": pick.player.team_name,
                "ruolo": "/".join(role.value.upper() for role in player_roles(pick.player)),
                "qi": pick.player.quote.qi,
                "punti": round(project(pick.player, league).total_points, 1),
                "aggiunte": ", ".join(str(week) for week in pick.added_weeks),
                "coperte": len(pick.covered_weeks),
                "costo": pick.cost,
            }
            for pick in picks
        ]
    )
    st.dataframe(
        frame,
        column_config={
            "nome": st.column_config.TextColumn("Prendi"),
            "squadra": st.column_config.TextColumn("Squadra"),
            "ruolo": st.column_config.TextColumn("Ruolo"),
            "qi": st.column_config.NumberColumn("QI"),
            "punti": st.column_config.NumberColumn("Punti attesi", format="%.1f"),
            "aggiunte": st.column_config.TextColumn("Giornate aggiunte"),
            "coperte": st.column_config.NumberColumn("Coperte cum."),
            "costo": st.column_config.NumberColumn("Costo cum."),
        },
        hide_index=True,
        width="stretch",
    )
    uncovered = [week for week in weeks if week not in picks[-1].covered_weeks]
    if uncovered:
        st.caption("Giornate ancora scoperte: " + ", ".join(str(w) for w in uncovered))


def main() -> None:
    st.title("FantaOptimizer")
    st.caption("Asta Serie A 2026/27 — regolamento Mantra")

    if "aggiorna_dati" not in st.session_state:
        st.session_state.aggiorna_dati = False

    _render_sidebar()
    _render_copertura_giocatore()


if __name__ == "__main__":
    main()
