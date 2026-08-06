"""FantaOptimizer — home: stato asta live + listone quotazioni.

La home gestisce la presa dei giocatori durante l'asta (budget e slot
residui, export/import stato) e il listone quotazioni con cache settimanale
e pulsante "Aggiorna dati" come unica via di invalidazione. Solo rendering
e input: la logica di rete/cache è delegata ai moduli data, il calcolo a
`logic` (entities/projection/optimize), lo stato a `state.py`.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from entities import GROUP_LABELS, ROLE_GROUP, ROLE_LABELS, Role, RoleGroup, TakenPick
from export_excel import build_report
from fetch_fixtures import get_calendario
from fetch_quotazioni import cache_mtime, get_quotazioni
from fetch_stats import get_statistiche
from optimize import ROSA_SLOTS, SpendingLimit, optimize_squad, spending_limit
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
    DEFAULT_MODULE,
    MODULES,
    CoverageRecommendation,
    UtilityScore,
    WeekSuggestion,
    coverage_recommendations,
    coverage_suggestions,
    easy_candidates,
    formation_positions,
    missing_roles,
    opponent_outlook,
    player_roles,
    team_strengths_from_players,
    utility_score,
    week_coverage,
)

logger = logging.getLogger(__name__)

st.set_page_config(page_title="FantaOptimizer", layout="wide")

QUOTAZIONI_COLUMNS = (
    "name",
    "team_name",
    "ruolo",
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
    frame = get_quotazioni(force_refresh=force)
    if frame.empty:
        return frame
    if "roles" in frame.columns:
        frame = frame.copy()
        frame["ruolo"] = frame["roles"].str.upper().str.replace(",", "/")
    else:
        frame["ruolo"] = frame.get("role_label", "")
    return frame


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
) -> tuple[SpendingLimit, UtilityScore, float, tuple[int, ...], bool]:
    """Consiglio per un giocatore (chiave = snapshot asta + modulo).

    Returns:
        (limite di spesa, utilità, punti attesi, giornate facili,
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
    easy_weeks = tuple(opp.matchweek for opp in outlook if opp.easy is True)
    has_results = league.league_gf_per_match is not None
    return limit, utility, points, easy_weeks, has_results


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


def _render_prese() -> None:
    """Tabella di tutte le prese dell'asta (ultima in cima)."""
    state = get_state()
    players = get_players(refresh_flag())
    name_by_url = {player.url: player.name for player in players}
    if not state.taken:
        return
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


def _render_formazione() -> None:
    """Modulo (condiviso con i consigli) e formazione disegnata con i presi."""
    st.write("#### Formazione")
    module = _module_selector()
    state = get_state()
    players = get_players(refresh_flag())
    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return
    own_urls = frozenset(pick.player_url for pick in state.taken if pick.owner == state.own_team)
    own_players = [p for p in players if p.url in own_urls]
    slots = slots_remaining(state, players)

    for line in formation_positions(module, own_players):
        st.caption(GROUP_LABELS[line.group])
        cols = st.columns(len(line.positions))
        for index, col in enumerate(cols):
            slot = line.positions[index]
            with col.container(border=True):
                if slot.player is not None:
                    st.markdown(f"**{slot.player.name}**")
                    st.caption(slot.player.team_name)
                    st.caption(_role_codes(player_roles(slot.player)))
                else:
                    st.markdown("—")
                    st.caption(ROLE_LABELS[slot.role])
        missing = missing_roles(line)
        if missing:
            st.caption("Mancano: " + ", ".join(ROLE_LABELS[Role(role)] for role in missing))
    owned = " · ".join(
        f"{GROUP_SHORT[group]} {ROSA_SLOTS[group] - slots.get(group, 0)}/{ROSA_SLOTS[group]}"
        for group in (RoleGroup.P, RoleGroup.D, RoleGroup.C, RoleGroup.A)
    )
    st.caption(f"Rosa presa: {owned} — il modulo si può cambiare in ogni momento.")


def _module_selector() -> str:
    """Selettore modulo persistente (sopravvive a `st.rerun()` parziali).

    Il widget è senza key: il valore vive in `session_state["modulo"]` come
    entry normale, che non viene ripulita quando un `st.rerun()` interrompe
    il run prima della creazione del widget (es. conferma presa,
    "Aggiorna dati").
    """
    options = list(MODULES)
    current = st.session_state.get("modulo")
    index = options.index(current) if current in MODULES else options.index(DEFAULT_MODULE)
    module = st.selectbox("Modulo", options, index=index)
    st.session_state.modulo = module
    return module


def _role_codes(roles: tuple[Role, ...]) -> str:
    """Codici ruolo compatti come sul listone (es. "E/W")."""
    return "/".join(role.value.upper() for role in roles)


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
    module = st.session_state.get("modulo", DEFAULT_MODULE)
    st.caption(f"Modulo: {module} — cambialo in tab Asta.")
    label = st.selectbox("Giocatore tra i rimasti", list(by_label), key="consigli_player")
    if not st.button("Calcola consiglio", key="consigli_run", type="primary"):
        return
    with st.spinner("Calcolo in corso (pochi secondi)..."):
        taken_tuple = tuple((pick.player_url, pick.owner, pick.price) for pick in state.taken)
        slots = slots_remaining(state, players)
        remaining = state.budget - spent_budget(state)
        limit, utility, points, easy_weeks, has_results = _advice_for(
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
    if easy_weeks:
        st.caption(f"Giornate facili: {', '.join(str(week) for week in easy_weeks)}")
    elif not has_results:
        st.caption(
            "Stagione non iniziata: forza squadra stimata dal listone — "
            "i consigli sul calendario diventano più precisi a campionato avviato."
        )
    else:
        st.caption("Nessun avversario facile tra le giornate rimanenti.")


@st.cache_data(show_spinner=False)
def _easy_at_week(
    matchweek: int,
    role_group: str,
    taken: tuple[tuple[str, str, int | None], ...],
    force: bool,
) -> tuple[tuple[str, str, str, int | None, float], ...]:
    """Rimasti con partita facile alla giornata (chiave = giornata + filtro).

    Returns:
        (nome, squadra, ruolo, qi, punti attesi) per ogni candidato.
    """
    players = get_players(force)
    league = get_league(force)
    calendars = get_calendars(force)
    strengths = team_strengths_from_players(players)
    taken_set = frozenset(url for url, _, _ in taken)
    remaining = [p for p in players if p.url not in taken_set]
    if role_group:
        group = RoleGroup(role_group)
        remaining = [p for p in remaining if ROLE_GROUP[p.role] is group]
    candidates = easy_candidates(matchweek, remaining, league, calendars, strengths)
    return tuple(
        (
            player.name,
            player.team_name,
            ROLE_LABELS[player.role],
            player.quote.qi,
            project(player, league).total_points,
        )
        for player in candidates
    )


@st.cache_data(show_spinner=False)
def _coverage_advice(
    taken: tuple[tuple[str, str, int | None], ...],
    own_team: str,
    force: bool,
) -> tuple[tuple[CoverageRecommendation, ...], tuple[WeekSuggestion, ...]]:
    """Consiglio diretto di copertura (chiave = snapshot prese).

    Returns:
        (classifica copertura, suggerimenti per giornata scoperta).
    """
    players = get_players(force)
    league = get_league(force)
    calendars = get_calendars(force)
    strengths = team_strengths_from_players(players)
    own_urls = frozenset(url for url, owner, _ in taken if owner == own_team)
    own_players = [p for p in players if p.url in own_urls]
    taken_set = frozenset(url for url, _, _ in taken)
    remaining = [p for p in players if p.url not in taken_set]
    return (
        coverage_recommendations(own_players, remaining, league, calendars, strengths),
        coverage_suggestions(own_players, remaining, league, calendars, strengths),
    )


def _fmt_weeks(weeks: tuple[int, ...]) -> str:
    """Giornate compatte: "12, 15, 18" (max 6, poi "…")."""
    if len(weeks) <= 6:
        return ", ".join(str(week) for week in weeks)
    return ", ".join(str(week) for week in weeks[:6]) + ", …"


def _render_copertura() -> None:
    """Copertura delle giornate facili per la rosa + ricerca inversa."""
    st.subheader("Copertura giornate facili")
    state = get_state()
    players = get_players(refresh_flag())
    if not players:
        st.info("Listone non ancora scaricato: premi 'Aggiorna dati'.")
        return
    league = get_league(refresh_flag())
    calendars = get_calendars(refresh_flag())
    strengths = team_strengths_from_players(players)
    own_urls = frozenset(pick.player_url for pick in state.taken if pick.owner == state.own_team)
    own_players = [p for p in players if p.url in own_urls]

    coverage = week_coverage(own_players, league, calendars, strengths)
    uncovered = sum(1 for week in coverage if week.uncovered)
    if coverage:
        frame = pd.DataFrame(
            [
                {
                    "giornata": week.matchweek,
                    "facili": week.easy_count,
                    "giocatori": week.present_count,
                    "stato": "scoperta" if week.uncovered else "",
                }
                for week in coverage
            ]
        )
        st.caption("Partite facili coperte per giornata (scoperta = presenti senza facili)")
        st.dataframe(frame, hide_index=True, width="stretch")
        if uncovered:
            st.caption(f"{uncovered} giornate scoperte: cerca qui sotto chi coprirle.")
    else:
        st.caption(
            "Nessun giocatore della tua squadra ancora: la copertura si attiva "
            "con le prime prese (la ricerca qui sotto funziona già)."
        )

    taken_tuple = tuple((pick.player_url, pick.owner, pick.price) for pick in state.taken)
    recommendations, suggestions = _coverage_advice(taken_tuple, state.own_team, refresh_flag())
    if recommendations:
        st.write("#### Consiglio diretto")
        if uncovered:
            st.caption("Chi copre più giornate scoperte della tua rosa:")
        else:
            st.caption(
                "Rosa senza giornate scoperte: chi ha più partite facili nelle giornate rimanenti."
            )
        for rec in recommendations:
            st.success(
                f"{rec.player.name} — {rec.player.team_name}: copre le giornate "
                f"{_fmt_weeks(rec.covered_weeks)} "
                f"({rec.points:.1f} punti attesi)"
            )
    if suggestions:
        st.write("#### Chi copre le giornate scoperte")
        suggestion_frame = pd.DataFrame(
            [
                {
                    "giornata": sug.matchweek,
                    "nome": sug.player.name,
                    "squadra": sug.player.team_name,
                    "punti": sug.points,
                }
                for sug in suggestions
            ]
        )
        st.dataframe(
            suggestion_frame,
            column_config={
                "giornata": st.column_config.NumberColumn("Giornata"),
                "nome": st.column_config.TextColumn("Consiglio"),
                "squadra": st.column_config.TextColumn("Squadra"),
                "punti": st.column_config.NumberColumn("Punti attesi", format="%.1f"),
            },
            hide_index=True,
            width="stretch",
        )

    if coverage:
        weeks = [week.matchweek for week in coverage]
        default_index = next((i for i, week in enumerate(coverage) if week.uncovered), 0)
    else:
        all_weeks = [cal.weeks for cal in calendars.values()]
        weeks = [week.matchweek for week in max(all_weeks, key=len)] if all_weeks else []
        default_index = 0
    if not weeks:
        st.info("Nessuna giornata valutabile: esegui 'Aggiorna dati'.")
        return
    col_week, col_role = st.columns(2)
    week_label = col_week.selectbox("Giornata", weeks, index=default_index, key="copertura_week")
    role_options = ["Tutti", *GROUP_LABELS.values()]
    role_label = col_role.selectbox("Ruolo", role_options, key="copertura_role")
    role_group = next(
        (group.value for group, label in GROUP_LABELS.items() if label == role_label),
        "",
    )
    rows = _easy_at_week(week_label, role_group, taken_tuple, refresh_flag())
    if not rows:
        st.info("Nessun giocatore rimasto con partita facile in questa giornata.")
        return
    candidates = pd.DataFrame(
        rows,
        columns=["name", "team", "role", "qi", "points"],
    ).sort_values("points", ascending=False)
    st.dataframe(
        candidates,
        column_config={
            "name": st.column_config.TextColumn("Nome"),
            "team": st.column_config.TextColumn("Squadra"),
            "role": st.column_config.TextColumn("Ruolo"),
            "qi": st.column_config.NumberColumn("QI"),
            "points": st.column_config.NumberColumn("Punti attesi", format="%.1f"),
        },
        hide_index=True,
        width="stretch",
    )
    st.caption(
        f"{len(candidates)} giocatori con partita facile alla giornata "
        f"{week_label} — ordinati per punti attesi"
    )


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
            "ruolo": st.column_config.TextColumn("Ruolo"),
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
    if "modulo" not in st.session_state:
        st.session_state.modulo = DEFAULT_MODULE

    _render_sidebar()

    tab_asta, tab_suggerimenti, tab_listone = st.tabs(["Asta", "Suggerimenti", "Listone"])
    with tab_asta:
        _render_stato_asta()
        _render_formazione()
        _render_prese()
    with tab_suggerimenti:
        _render_consigli()
        _render_copertura()
    with tab_listone:
        _render_quotazioni()


if __name__ == "__main__":
    main()
