"""FantaOptimizer — schermata unica: il listone completo.

Una sola pagina con tutte le informazioni del file `Listone.xlsx`
(ruoli Mantra, squadra, titolarità, FMV, rigorista, punizioni, angoli,
presi), con ricerca e filtri. Solo rendering e input: la lettura del file
è delegata al layer data (`fetch_listone`), lo stato a `state.py`.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

try:
    from entities import GROUP_LABELS, ROLE_GROUP, RoleGroup
    from export_excel import build_report
    from fetch_fixtures import get_calendario
    from fetch_quotazioni import get_quotazioni
    from fetch_stats import get_statistiche
    from optimize import optimize_squad
    from state import export_state, import_state
    from ui_common import (
        get_league,
        get_listone,
        get_players,
        get_state,
        refresh_flag,
        role_codes,
        set_state,
        slot_tuple,
        state_snapshot,
    )
    from utility import LOGIC_VERSION
except ImportError as exc:
    logger.exception("Deploy incompleto: import falliti al boot (%s)", exc)
    st.error(
        "Deploy incompleto: il server sta servendo file di versioni diverse. "
        "Chiudi l'app, eliminala e ricreala su Streamlit Cloud (Delete app → "
        "Create app dallo stesso repository, branch `deploy`), poi riapri — "
        "la versione corretta è mostrata nel titolo."
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


def _app_version() -> str:
    """Versione deployata (da version.txt), per la diagnosi."""
    try:
        return Path("version.txt").read_text(encoding="utf-8").strip()
    except OSError:
        return "?"


def deploy_ok(version_file: Path = Path("version.txt")) -> bool:
    """Vero se il deploy è coerente: `version.txt` == versione della logica.

    Streamlit Cloud può servire file di commit diversi (main.py nuovo con
    `utility.py` vecchia): il confronto rende il deploy misto visibile
    subito invece di produrre numeri sbagliati in silenzio.
    """
    try:
        return version_file.read_text(encoding="utf-8").strip() == LOGIC_VERSION
    except OSError:
        return False


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


def _render_listone() -> None:
    """Il listone completo con ricerca, filtri squadra/gruppo e tutte le info."""
    st.subheader("Listone")
    rows = get_listone(refresh_flag())
    if not rows:
        st.info("Listone non ancora presente: copia il file Listone.xlsx in resources/.")
        return

    search = st.text_input("Cerca giocatore", key="listone_search")
    teams = sorted({row.team_name for row in rows})
    team = st.selectbox("Squadra", ["Tutte", *teams], key="listone_team")
    group_labels = {group: label for group, label in GROUP_LABELS.items()}
    group = st.selectbox("Gruppo ruolo", ["Tutti", *group_labels.values()], key="listone_group")

    filtered = rows
    if search.strip():
        needle = search.strip().lower()
        filtered = [row for row in filtered if needle in row.name.lower()]
    if team != "Tutte":
        filtered = [row for row in filtered if row.team_name == team]
    if group != "Tutti":
        selected = next(role_group for role_group, label in group_labels.items() if label == group)
        filtered = [
            row for row in filtered if any(ROLE_GROUP[role] is selected for role in row.roles)
        ]

    st.dataframe(
        _listone_frame(filtered),
        column_config={
            "giocatore": st.column_config.TextColumn("Giocatore"),
            "ruoli": st.column_config.TextColumn("Ruolo"),
            "squadra": st.column_config.TextColumn("Squadra"),
            "titolarita": st.column_config.NumberColumn("Titolarità %", format="%.0f"),
            "fmv": st.column_config.NumberColumn("FMV", format="%.2f"),
            "rigorista": st.column_config.TextColumn("Rigorista"),
            "punizioni": st.column_config.TextColumn("Punizioni"),
            "angoli": st.column_config.TextColumn("Angoli"),
            "preso_noi": st.column_config.TextColumn("Preso noi"),
            "preso_altri": st.column_config.TextColumn("Preso altri"),
        },
        hide_index=True,
        width="stretch",
    )
    st.caption(f"{len(filtered)} giocatori su {len(rows)}")


def _listone_frame(rows: tuple) -> pd.DataFrame:
    """Frame del listone con tutte le informazioni del file Excel."""
    return pd.DataFrame(
        [
            {
                "giocatore": row.name,
                "ruoli": role_codes(row.roles),
                "squadra": row.team_name,
                "titolarita": row.titolarita,
                "fmv": row.fmv,
                "rigorista": _flag(row.rigorista),
                "punizioni": _flag(row.punizioni),
                "angoli": _flag(row.angoli),
                "preso_noi": _flag(row.preso_noi),
                "preso_altri": _flag(row.preso_altri),
            }
            for row in rows
        ]
    )


def _flag(value: bool) -> str:
    """Spunta del listone (vuoto se assente)."""
    return "✔" if value else ""


def main() -> None:
    st.title(f"FantaOptimizer — v{_app_version()}")
    st.caption("Asta Serie A 2026/27 — regolamento Mantra")

    if not deploy_ok():
        st.error(
            f"Deploy misto: la versione del deploy ({_app_version()}) non "
            f"corrisponde alla logica ({LOGIC_VERSION}): il server sta servendo "
            "file di commit diversi e i calcoli possono essere sbagliati. "
            "Chiudi l'app, eliminala e ricreala su Streamlit Cloud (Delete app "
            "→ Create app dallo stesso repository, branch `deploy`), oppure "
            "cambia il branch in dashboard per forzare un checkout pulito."
        )
        st.stop()

    if "aggiorna_dati" not in st.session_state:
        st.session_state.aggiorna_dati = False

    _render_sidebar()
    _render_listone()


if __name__ == "__main__":
    main()
