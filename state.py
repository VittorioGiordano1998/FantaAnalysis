"""Stato dell'asta: persistenza JSON locale e import/export bytes (ADR-0004).

Modulo del layer `data`: è l'unico che legge/scrive il JSON di stato e fa
import/export. Le mutazioni sono funzioni pure che restituiscono un nuovo
`AuctionState` frozen; i valori derivati (budget speso, slot residui) si
ricavano da `taken` + giocatori.

Su Streamlit Cloud il disco è effimero: la fonte di verità è il round-trip
via `export_state`/`import_state`; `data/asta.json` è solo convenienza
locale.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

from entities import ROLE_GROUP, AuctionState, Player, RoleGroup, TakenPick
from optimize import DEFAULT_BUDGET, ROSA_SLOTS

logger = logging.getLogger(__name__)

STATE_FILE = Path("data") / "asta.json"
_VERSION = 1


def default_state(budget: int = DEFAULT_BUDGET) -> AuctionState:
    """Stato d'asta iniziale: budget pieno, nessuna presa.

    Args:
        budget: budget totale di partenza (default 500).

    Returns:
        `AuctionState` vuoto.
    """
    return AuctionState(budget=budget)


def load_state(path: Path | None = None) -> AuctionState:
    """Legge lo stato dal file (default `data/asta.json`).

    File assente → stato iniziale.

    Args:
        path: percorso del JSON (per i test, `tmp_path`).

    Returns:
        Stato salvato oppure `default_state()`.
    """
    state_file = path or STATE_FILE
    if not state_file.is_file():
        return default_state()
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("Stato asta corrotto in %s: riparto da zero", state_file)
        return default_state()
    return _from_payload(payload)


def save_state(state: AuctionState, path: Path | None = None) -> None:
    """Scrive lo stato su JSON (utf-8), creando la directory se serve.

    Args:
        state: stato da salvare.
        path: percorso di destinazione (default `data/asta.json`).
    """
    state_file = path or STATE_FILE
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(_to_payload(state), ensure_ascii=False), encoding="utf-8")


def export_state(state: AuctionState) -> bytes:
    """Serializza lo stato in bytes JSON (percorso ufficiale su Cloud).

    Args:
        state: stato da esportare.

    Returns:
        Bytes JSON utf-8 versionati (ADR-0004).
    """
    return json.dumps(_to_payload(state), ensure_ascii=False, indent=2).encode("utf-8")


def import_state(data: bytes) -> AuctionState:
    """Ricostruisce lo stato da bytes JSON (percorso ufficiale su Cloud).

    Args:
        data: bytes prodotti da `export_state`.

    Returns:
        Stato importato.

    Raises:
        ValueError: se il payload è malformato (JSON, versione o forma).
    """
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("file di stato non valido") from exc
    return _from_payload(payload)


def add_taken(state: AuctionState, pick: TakenPick) -> AuctionState:
    """Aggiunge una presa all'asta (ADR-0004).

    Args:
        state: stato corrente.
        pick: giocatore preso (URL, owner, prezzo pagato).

    Returns:
        Nuovo stato con la presa in coda.

    Raises:
        ValueError: se il giocatore è già stato preso.
    """
    if any(existing.player_url == pick.player_url for existing in state.taken):
        raise ValueError(f"giocatore già preso: {pick.player_url}")
    return AuctionState(
        budget=state.budget,
        own_team=state.own_team,
        taken=(*state.taken, pick),
    )


def remove_taken(state: AuctionState, player_url: str) -> AuctionState:
    """Rimuove una presa dallo stato.

    Args:
        state: stato corrente.
        player_url: giocatore da liberare.

    Returns:
        Nuovo stato senza la presa (invariato se non presente).
    """
    return AuctionState(
        budget=state.budget,
        own_team=state.own_team,
        taken=tuple(pick for pick in state.taken if pick.player_url != player_url),
    )


def taken_urls(state: AuctionState) -> frozenset[str]:
    """URL di tutti i giocatori presi (pool escluso dall'ottimizzatore)."""
    return frozenset(pick.player_url for pick in state.taken)


def spent_budget(state: AuctionState) -> int:
    """Crediti spesi per la propria squadra (prese con owner = own_team).

    Args:
        state: stato corrente.

    Returns:
        Somma dei prezzi pagati per la propria squadra (None → 0).
    """
    return sum(pick.price or 0 for pick in state.taken if pick.owner == state.own_team)


def slots_remaining(
    state: AuctionState,
    players: Sequence[Player],
    slots: Mapping[RoleGroup, int] = ROSA_SLOTS,
) -> dict[RoleGroup, int]:
    """Slot per gruppo ancora liberi per la propria squadra (ADR-0004).

    Args:
        state: stato corrente.
        players: giocatori del listone (per il ruolo, via URL).
        slots: slot di rosa per gruppo (default rosa 2P-8D-8C-7A).

    Returns:
        Slot rimanenti per gruppo ruolo (minimo 0).
    """
    role_by_url = {player.url: player.role for player in players}
    own_picks = [
        pick
        for pick in state.taken
        if pick.owner == state.own_team and pick.player_url in role_by_url
    ]
    remaining = dict(slots)
    for pick in own_picks:
        group = ROLE_GROUP[role_by_url[pick.player_url]]
        remaining[group] = max(0, remaining[group] - 1)
    return remaining


def _to_payload(state: AuctionState) -> dict[str, object]:
    """Stato → dict JSON versionato (ADR-0004)."""
    return {
        "version": _VERSION,
        "budget": state.budget,
        "own_team": state.own_team,
        "taken": [[pick.player_url, pick.owner, pick.price] for pick in state.taken],
    }


def _from_payload(payload: object) -> AuctionState:
    """dict JSON → stato, con validazione (malformato → ValueError)."""
    if not isinstance(payload, dict) or payload.get("version") != _VERSION:
        raise ValueError("formato di stato non supportato")
    try:
        budget = int(payload["budget"])
        own_team = str(payload["own_team"])
        raw_taken = payload["taken"]
        if budget <= 0 or not isinstance(raw_taken, list):
            raise TypeError
        taken = tuple(_from_pick(raw) for raw in raw_taken)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("file di stato non valido") from exc
    return AuctionState(budget=budget, own_team=own_team, taken=taken)


def _from_pick(raw: object) -> TakenPick:
    """Una presa dal JSON (lista di 2-3 elementi), validata."""
    if not isinstance(raw, list) or len(raw) not in (2, 3):
        raise ValueError
    url, owner = str(raw[0]), str(raw[1])
    price = int(raw[2]) if len(raw) == 3 and raw[2] is not None else None
    if not url or not owner:
        raise ValueError
    return TakenPick(player_url=url, owner=owner, price=price)
