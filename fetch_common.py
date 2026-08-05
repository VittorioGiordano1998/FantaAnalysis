"""Helper condivisi per i moduli fetch_* del layer data.

Rete (User-Agent identificativo, timeout, rate-limit tra richieste),
conversione di numeri in formato italiano (virgola decimale), freschezza
della cache e I/O CSV/DataFrame.
"""

from __future__ import annotations

import csv
import logging
import time
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "FantaOptimizer/0.1 (https://github.com/FantaOptimizer)"
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_DELAY_SECONDS = 1.0


def fetch_html(url: str, session: requests.Session | None = None) -> str:
    """Scarica una pagina con User-Agent identificativo e rate-limit.

    Args:
        url: indirizzo da scaricare.
        session: sessione requests riutilizzabile (per i test).

    Returns:
        Il testo HTML della risposta.

    Raises:
        requests.HTTPError: se il server risponde con un errore.
    """
    http = session or requests
    response = http.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    time.sleep(REQUEST_DELAY_SECONDS)
    return response.text


def to_int(raw: str | None) -> int | None:
    """Converte testo numerico in int, tollerando celle vuote o non numeriche."""
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def to_decimal(raw: str | None) -> float | None:
    """Converte testo numerico decimale (virgola italiana) in float."""
    if raw is None:
        return None
    text = raw.strip().replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def is_cache_fresh(
    path: Path,
    max_age_days: int,
    now: datetime | None = None,
) -> bool:
    """True se la cache esiste ed è più giovane di `max_age_days` giorni."""
    if not path.is_file():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime > (now or datetime.now()) - timedelta(days=max_age_days)


def read_cache_frame(path: Path) -> pd.DataFrame:
    """Legge il CSV di cache (utf-8-sig) come DataFrame."""
    return pd.read_csv(path, encoding="utf-8-sig")


def write_csv(
    rows: Iterable[Mapping[str, object]],
    path: Path,
    columns: tuple[str, ...],
) -> None:
    """Scrive righe (dizionari) su CSV utf-8-sig, leggibile da Excel.

    Args:
        rows: righe da serializzare, una per elemento.
        path: percorso di destinazione (la dir padre viene creata).
        columns: intestazioni (devono coprire tutte le chiavi di `rows`).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
