"""FantaOptimizer — home: stato asta live + listone quotazioni.

La home gestisce la presa dei giocatori durante l'asta (budget e slot
residui, export/import stato) e il listone quotazioni con cache settimanale
e pulsante "Aggiorna dati" come unica via di invalidazione. Solo rendering
e input: la logica di rete/cache è delegata ai moduli data, il calcolo a
`logic` (entities/projection/optimize), lo stato a `state.py`.
"""

import logging

import pandas as pd
import streamlit as st

from entities import RoleGroup, TakenPick
from export_excel import build_report
from fetch_fixtures import get_calendario
from fetch_quotazioni import cache_mtime, get_quotazioni
from fetch_stats import get_statistiche
from optimize import SpendingLimit, optimize_squad, spending_limit
from projection import project
from state import (
    add_taken,
    export_state,
    import_state,
    remove_taken,
    slots_remaining,
    spent_budget,
    taken_urls,
)
from ui_common import (
    get_calendars,
    get_league,
    get_players,
    get_state,
    refresh_flag,
    set_state,
    slot_tuple,
    state_snapshot,
)
from utility import (
    MODULES,
    UtilityScore,
    opponent_outlook,
    team_strengths_from_players,
    utility_score,
)

logger = logging.getLogger(__name__)

st.set_page_config(page_title="FantaOptimizer", layout="wide")

QUOTAZIONI_COLUMNS = (
    "name",
    "team_name",
    "role_label",
    "qi",
    "qa",
    "fvm",
)

OWNER_OTHER = "Avversario"

GROUP_SHORT = {
    RoleGroup.P: "P",
    RoleGroup.D: "D",
    RoleGroup.C: "C",
    RoleGroup.A: "A",
}


@st.cache_data(show_spinner=False)
def _load_quotazioni(force: bool) -> pd.DataFrame:
    """Carica le quotazioni dalla cache CSV, chiave = flag aggiornamento."""
    return get_quotazioni(force_refresh=force)


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
def _advice_for(
    player_url: str,
    taken: tuple[tuple[str, str, int | None], ...],
    budget: int,
    slots: tuple[tuple[str, int], ...],
    own_team: str,
    module: str,
    force: bool,
) -> tuple[SpendingLimit, UtilityScore, float, tuple[str, ...], bool]:
    """Consiglio per un giocatore (chiave = snapshot asta + modulo).

    Returns:
        (limite di spesa, utilità, punti attesi, avversari facili,
        medie di lega disponibili).
    """
    players = get_players(force)
    league = get_league(force)
    player = next(p for p in players if p.url == player_url)
    taken_set = frozenset(url for url, _, _ in taken)
    slots_map = {RoleGroup(name): count for name, count in slots}
    limit = spending_limit(
        player,
        players,
        league,
        budget=budget,
        slots=slots_map,
        taken_urls=taken_set,
    )
    own_urls = frozenset(url for url, owner, _ in taken if owner == own_team)
    own_players = [p for p in players if p.url in own_urls]
    calendars = get_calendars(force)
    strengths = team_strengths_from_players(players)
    utility = utility_score(
        player,
        league,
        slots_map,
        own_players,
        module,
        calendars,
        strengths,
    )
    points = project(player, league).total_points
    outlook = opponent_outlook(player, league, calendars, strengths)
    easy = tuple(opp.team_name for opp in outlook if opp.easy is True)
    has_results = league.league_gf_per_match is not None
    return limit, utility, points, easy, has_results


def _render_aggiorna_dati() -> None:
    """Pulsante "Aggiorna dati": unica via di invalidazione delle cache."""
    if st.button("Aggiorna dati"):
        with st.spinner("Aggiornamento dati in corso..."):
            get_quotazioni(force_refresh=True)
            get_statistiche(force_refresh=True)
            get_calendario(force_refresh=True)
        st.session_state.aggiorna_dati = not st.session_state.aggiorna_dati
        st.rerun()


def _render_stato_asta() -> None:
    """Stato asta: budget/slot residui, presa e annullamento giocatori."""
    st.subheader("Stato asta")
    state = get_state()
    players = get_players(refresh_flag())
    spent = spent_budget(state)
    remaining = state.budget - spent
    slots = slots_remaining(state, players)

    col_budget, col_slots = st.columns(2)
    col_budget.metric("Budget residuo", f"{remaining} / {state.budget}")
    col_slots.caption(
        "Slot rimasti: " + " — ".join(f"{GROUP_SHORT[g]} {n}" for g, n in slots.items())
    )

    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return

    name_by_url = {player.url: player.name for player in players}
    taken = taken_urls(state)

    st.write("#### Prendi giocatore")
    by_label = _player_labels(players, taken)
    if not by_label:
        st.info("Tutti i giocatori del listone sono già presi.")
        return
    label = st.selectbox("Giocatore", list(by_label), key="pick_player")
    owner = st.segmented_control(
        "Squadra che prende",
        [state.own_team, OWNER_OTHER],
        default=state.own_team,
        key="pick_owner",
    )
    price = 0
    if owner == state.own_team:
        price = st.number_input(
            "Prezzo pagato",
            min_value=0,
            max_value=remaining,
            value=0,
            step=1,
            key="pick_price",
        )
    if st.button("Conferma presa", key="pick_confirm"):
        try:
            set_state(
                add_taken(
                    state,
                    TakenPick(
                        player_url=by_label[label],
                        owner=owner,
                        price=int(price) if owner == state.own_team else None,
                    ),
                )
            )
            st.rerun()
        except ValueError:
            st.error("Giocatore già preso: selezionane un altro.")

    if state.taken:
        st.write("#### Annulla presa")
        undo_by_label = {
            f"{name_by_url.get(pick.player_url, pick.player_url)} ({pick.owner})": pick.player_url
            for pick in state.taken
        }
        undo_label = st.selectbox("Giocatore da liberare", list(undo_by_label), key="undo_player")
        if st.button("Libera giocatore", key="undo_confirm"):
            set_state(remove_taken(state, undo_by_label[undo_label]))
            st.rerun()

        st.write("#### Prese")
        frame = pd.DataFrame(
            [
                {
                    "squadra": pick.owner,
                    "giocatore": name_by_url.get(pick.player_url, pick.player_url),
                    "prezzo": pick.price if pick.price is not None else "—",
                }
                for pick in reversed(state.taken)
            ]
        )
        st.dataframe(frame, hide_index=True, width="stretch")


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


def _render_consigli() -> None:
    """Consigli di acquisto: prezzo max, utilità e calendario per giocatore."""
    st.subheader("Consigli di acquisto")
    state = get_state()
    players = get_players(refresh_flag())
    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return
    taken = taken_urls(state)
    by_label = _player_labels(players, taken)
    if not by_label:
        st.info("Tutti i giocatori del listone sono già presi.")
        return
    col_module, col_player = st.columns([1, 3])
    module = col_module.selectbox("Modulo", list(MODULES), key="consigli_module")
    label = col_player.selectbox(
        "Giocatore tra i rimasti", list(by_label), key="consigli_player"
    )
    if not st.button("Calcola consiglio", key="consigli_run", type="primary"):
        return
    with st.spinner("Calcolo in corso (pochi secondi)..."):
        taken_tuple = tuple(
            (pick.player_url, pick.owner, pick.price) for pick in state.taken
        )
        slots = slots_remaining(state, players)
        remaining = state.budget - spent_budget(state)
        limit, utility, points, easy, has_results = _advice_for(
            by_label[label],
            taken_tuple,
            remaining,
            slot_tuple(slots),
            state.own_team,
            module,
            refresh_flag(),
        )
    player_name = label.rsplit(" — ", 1)[0]
    if limit.status != "Optimal":
        st.warning("Rosa di base non realizzabile: nessun limite calcolabile.")
    else:
        st.success(f"Offri al massimo {limit.max_price} crediti per {player_name}.")
    st.metric("Utilità", f"{utility.score * 100:.0f}%")
    st.caption(
        f"Slot: {utility.slot_need * 100:.0f}% · "
        f"Calendario: {utility.calendar_ease * 100:.0f}% · "
        f"Copertura: {utility.coverage * 100:.0f}%"
    )
    if easy:
        st.caption(f"Avversari facili: {', '.join(easy)}")
    elif not has_results:
        st.caption(
            "Stagione non iniziata: forza squadra stimata dal listone — "
            "i consigli sul calendario diventano più precisi a campionato avviato."
        )
    else:
        st.caption("Nessun avversario facile tra le giornate rimanenti.")


def _render_quotazioni() -> None:
    """Listone quotazioni con data di aggiornamento."""
    st.subheader("Listone quotazioni")
    frame = _load_quotazioni(refresh_flag())
    if frame.empty:
        st.info("Nessun dato disponibile: premi 'Aggiorna dati'.")
        return
    last_update = cache_mtime()
    if last_update is not None:
        st.caption(f"Ultimo aggiornamento: {last_update:%d/%m/%Y %H:%M}")

    st.dataframe(
        frame[list(QUOTAZIONI_COLUMNS)],
        column_config={
            "name": st.column_config.TextColumn("Nome"),
            "team_name": st.column_config.TextColumn("Squadra"),
            "role_label": st.column_config.TextColumn("Ruolo"),
            "qi": st.column_config.NumberColumn("QI"),
            "qa": st.column_config.NumberColumn("QA"),
            "fvm": st.column_config.NumberColumn("FVM"),
        },
        hide_index=True,
        width="stretch",
    )


def _player_labels(players: list, taken: frozenset[str]) -> dict[str, str]:
    """Etichetta "Nome — Squadra" → URL, per i giocatori ancora disponibili."""
    return {
        f"{player.name} — {player.team_name}": player.url
        for player in players
        if player.url not in taken
    }


def main() -> None:
    st.title("FantaOptimizer")
    st.caption("Asta Serie A 2026/27 — regolamento Mantra")

    if "aggiorna_dati" not in st.session_state:
        st.session_state.aggiorna_dati = False

    _render_export_import()
    _render_report()
    _render_aggiorna_dati()
    _render_stato_asta()
    _render_consigli()
    _render_quotazioni()


if __name__ == "__main__":
    main()
