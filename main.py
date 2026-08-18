"""FantaOptimizer — schermata unica: listone a tutto schermo con colori.

Una sola pagina senza chrome: il listone completo dal file
`resources/listone.xlsx` con le stesse regole di colore del file Excel
(riga presa da noi = verde, presa da altri = rosso; titolarità e FMV
colorati per valore). Solo rendering e input: la lettura del file è
delegata al layer data (`fetch_listone`).
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.io.formats.style import Styler

from ui_common import get_listone, refresh_flag, role_codes
from utility import LOGIC_VERSION

logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="FantaOptimizer",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Chrome di Streamlit nascosto: il listone occupa tutto lo schermo.
_FULL_SCREEN_CSS = """
<style>
header[data-testid="stHeader"] { display: none; }
[data-testid="stToolbar"] { display: none; }
[data-testid="stDecoration"] { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.block-container { padding: 0 0.5rem; max-width: 100%; }
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


def _row_style(row: pd.Series) -> list[str]:
    """Colore di riga come in Excel: presa da noi verde, da altri rosso."""
    if row["preso_noi"] == "✔":
        color = ROW_TAKEN_NOI
    elif row["preso_altri"] == "✔":
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


def _style_frame(frame: pd.DataFrame) -> Styler:
    """Styler con le regole di colore del file Excel.

    Ordine come in Excel: le regole di cella (titolarità, FMV, priorità
    più alta) vincono sul colore di riga nelle loro colonne.
    """
    return (
        frame.style.apply(_row_style, axis=1)
        .map(_titolarita_style, subset=["titolarita"])
        .map(_fmv_style, subset=["fmv"])
    )


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
    st.dataframe(
        _style_frame(_listone_frame(rows)),
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
        height="stretch",
    )


if __name__ == "__main__":
    main()
