"""FantaOptimizer — schermata unica: listone a tutto schermo con colori.

Una sola pagina senza chrome: il listone completo dal file
`resources/listone.xlsx` con le stesse regole di colore del file Excel
(riga presa da noi = verde, presa da altri = rosso; titolarità e FMV
colorati per valore). Le prese si segnano selezionando le righe e
premendo i pulsanti "Preso da noi" / "Preso da altri", indicando il
prezzo pagato: il budget residuo è calcolato e mostrato in alto. Lo
stato vive in `data/listone_flags.json` (`state.py`), i flag del file
Excel restano la base. Solo rendering e input: la lettura del file è
delegata al layer data (`fetch_listone`).
"""

from collections.abc import Sequence
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from entities import ListoneState
from state import listone_remaining, load_listone_flags, save_listone_flags
from ui_common import get_listone, refresh_flag, role_codes
from utility import LOGIC_VERSION

st.set_page_config(
    page_title="FantaOptimizer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Chrome di Streamlit nascosto e tabella che riempie lo schermo fino in fondo.
_FULL_SCREEN_CSS = """
<style>
header[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.block-container { padding: 0 0.5rem; max-width: 100%; }
[data-testid="stDataFrame"] { height: 100vh !important; }
[data-testid="stDataFrameResizable"] { height: calc(100vh - 3.5rem) !important; }
</style>
"""

# Regole copiate dal file Listone.xlsx (Foglio1, formattazione condizionale):
# - riga presa da noi -> verde, presa da altri -> rosso (espressioni $T2/$U2);
# - titolarità: 95 -> verde, 75 -> giallo, 50 -> arancio, 25 -> rosso;
# - FMV: >= 6 -> verde, < 6 -> rosso.
ROW_TAKEN_NOI = "#B7E1CD"
ROW_TAKEN_ALTRI = "#E06666"
TITOLARITA_COLORS = {95: "#93C47D", 75: "#FFD966", 50: "#E69138", 25: "#E06666"}
FMV_MIN_OK = 6
FMV_OK_COLOR = "#93C47D"
FMV_LOW_COLOR = "#E06666"

FLAGS_KEY = "listone_flags"


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


def _row_style(row: pd.Series, stati: Sequence[str]) -> list[str]:
    """Colore di riga come in Excel: presa da noi verde, da altri rosso."""
    stato = stati[row.name] if row.name < len(stati) else ""
    if stato == "noi":
        color = ROW_TAKEN_NOI
    elif stato == "altri":
        color = ROW_TAKEN_ALTRI
    else:
        color = ""
    return [f"background-color: {color}" if color else ""] * len(row)


def _titolarita_style(value) -> str:
    """Colore della cella titolarità per soglia, come nel file Excel."""
    color = TITOLARITA_COLORS.get(value)
    return f"background-color: {color}" if color else ""


def _fmv_style(value) -> str:
    """Colore della cella FMV per soglia (>= 6 verde, altrimenti rosso)."""
    if value is None:
        return ""
    color = FMV_OK_COLOR if value >= FMV_MIN_OK else FMV_LOW_COLOR
    return f"background-color: {color}"


def _style_frame(frame: pd.DataFrame, stati: Sequence[str]) -> Styler:
    """Styler con le regole di colore del file Excel.

    `stati` è il vettore parallelo (stessa posizione delle righe) con lo
    stato di presa. Ordine come in Excel: le regole di cella (titolarità,
    FMV, priorità più alta) vincono sul colore di riga nelle loro colonne.
    """
    return (
        frame.style.apply(_row_style, axis=1, stati=stati)
        .map(_titolarita_style, subset=["titolarita"])
        .map(_fmv_style, subset=["fmv"])
    )


def _merged_flag(excel_noi: bool, excel_altri: bool, session: str | None) -> str:
    """Stato di presa della riga: sessione (se presente) poi file Excel."""
    if session is not None:
        return session
    if excel_noi:
        return "noi"
    if excel_altri:
        return "altri"
    return ""


def _needs_price(state: ListoneState, names: Sequence[str], price: int) -> bool:
    """Vero se il mark "noi" richiede un prezzo (almeno un giocatore nuovo)."""
    return price <= 0 and any(state.flags.get(name) != "noi" for name in names)


def _toggle_flags(
    state: ListoneState,
    names: Sequence[str],
    owner: str,
    price: int | None = None,
) -> ListoneState:
    """Alterna le prese dei giocatori selezionati (noi/altri/libero).

    Segnando "noi" con un prezzo il prezzo viene registrato; liberando o
    passando ad "altri" il prezzo viene rimosso.
    """
    flags = dict(state.flags)
    prices = dict(state.prices)
    for name in names:
        if flags.get(name) == owner:
            flags[name] = ""
            prices.pop(name, None)
        else:
            flags[name] = owner
            if owner == "noi" and price:
                prices[name] = price
            else:
                prices.pop(name, None)
    return ListoneState(budget=state.budget, flags=flags, prices=prices)


def _listone_frame(rows: tuple, state: ListoneState) -> pd.DataFrame:
    """Frame del listone con tutte le informazioni del file Excel.

    La colonna "stato" (presa effettiva) non viene mostrata: alimenta solo
    il colore di riga. La colonna "prezzo" mostra quanto pagato per i
    presi da noi.
    """
    return pd.DataFrame(
        [
            {
                "giocatore": row.name,
                "ruoli": role_codes(row.roles),
                "squadra": row.team_name,
                "titolarita": row.titolarita,
                "fmv": row.fmv,
                "rigorista": row.rigorista,
                "punizioni": row.punizioni,
                "angoli": row.angoli,
                "prezzo": _price(row.name, state),
                "stato": _merged_flag(row.preso_noi, row.preso_altri, state.flags.get(row.name)),
            }
            for row in rows
        ]
    )


def _price(name: str, state: ListoneState) -> int | None:
    """Prezzo pagato per il giocatore, se preso dalla propria squadra."""
    if state.flags.get(name) != "noi":
        return None
    return state.prices.get(name)


def main() -> None:
    if not deploy_ok():
        st.error(
            f"Deploy misto: la versione del deploy ({_app_version()}) non "
            f"corrisponde alla logica ({LOGIC_VERSION}): il server sta servendo "
            "file di commit diversi. Chiudi l'app, eliminala e ricreala su "
            "Streamlit Cloud (Delete app → Create app dallo stesso repository, "
            "branch `deploy`), oppure cambia il branch in dashboard per forzare "
            "un checkout pulito."
        )
        st.stop()
    st.markdown(_FULL_SCREEN_CSS, unsafe_allow_html=True)
    rows = get_listone(refresh_flag())
    if not rows:
        st.info("Listone non presente: copia il file Listone.xlsx in resources/.")
        return
    if FLAGS_KEY not in st.session_state:
        st.session_state[FLAGS_KEY] = load_listone_flags()
    state = st.session_state[FLAGS_KEY]
    frame = _listone_frame(rows, state)
    stati = tuple(frame.pop("stato"))

    price_row = st.columns(2)
    with price_row[0]:
        if "price_mount" not in st.session_state:
            st.session_state.price_mount = 0
        price = st.number_input(
            "Prezzo pagato (crediti)",
            min_value=0,
            value=0,
            step=1,
            key=f"price_paid_{st.session_state.price_mount}",
        )
    with price_row[1]:
        budget = st.number_input(
            "Budget totale (crediti)",
            min_value=1,
            value=state.budget,
            step=5,
            key="budget_total",
        )
    if budget != state.budget:
        state = ListoneState(budget=budget, flags=dict(state.flags), prices=dict(state.prices))
        st.session_state[FLAGS_KEY] = state
        save_listone_flags(state)

    toolbar = st.columns([1, 1, 3], vertical_alignment="center")
    with toolbar[0]:
        mark_noi = st.button("Preso da noi", key="mark_noi", width="stretch")
    with toolbar[1]:
        mark_altri = st.button("Preso da altri", key="mark_altri", width="stretch")
    with toolbar[2]:
        remaining = listone_remaining(state)
        budget_text = (
            f"Residuo: {remaining} / {state.budget} crediti"
            if remaining >= 0
            else f"Sei sopra budget di {-remaining} crediti"
        )
        st.caption(f"{budget_text} — verde = preso da noi, rosso = preso da altri.")

    selection = st.dataframe(
        _style_frame(frame, stati),
        column_config={
            "giocatore": st.column_config.TextColumn("Giocatore"),
            "ruoli": st.column_config.TextColumn("Ruolo"),
            "squadra": st.column_config.TextColumn("Squadra"),
            "titolarita": st.column_config.NumberColumn("Titolarità %", format="%.0f"),
            "fmv": st.column_config.NumberColumn("FMV", format="%.2f"),
            "rigorista": st.column_config.NumberColumn("Rigorista", format="%d"),
            "punizioni": st.column_config.NumberColumn("Punizioni", format="%d"),
            "angoli": st.column_config.NumberColumn("Angoli", format="%d"),
            "prezzo": st.column_config.NumberColumn("Prezzo", format="%d"),
        },
        hide_index=True,
        width="stretch",
        height="stretch",
        on_select="rerun",
        selection_mode="multi-row",
    ).selection.rows
    names = [frame.iloc[index]["giocatore"] for index in selection]

    if mark_noi or mark_altri:
        if not names:
            st.warning("Seleziona prima una o più righe dalla tabella.")
        elif mark_noi and _needs_price(state, names, int(price)):
            st.warning("Inserisci il prezzo pagato (crediti) prima di segnare 'Preso da noi'.")
        else:
            state = _toggle_flags(state, names, "noi" if mark_noi else "altri", int(price))
            st.session_state[FLAGS_KEY] = state
            save_listone_flags(state)
            st.session_state.price_mount += 1
            st.rerun()


if __name__ == "__main__":
    main()
