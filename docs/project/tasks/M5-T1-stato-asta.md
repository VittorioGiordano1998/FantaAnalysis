# Task: M5-T1 — Stato asta: modello e persistenza

- **ID:** M5-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** data

## Problem

PLANNING §2 (#1, #5): serve lo stato asta live (presi tua squadra / altre,
budget speso/residuo, slot per ruolo) con persistenza JSON locale e
import/export via bytes (Streamlit Cloud senza disco persistente). Oggi non
esiste né il modello né il modulo di persistenza.

## Proposed Solution

- ADR-0004: forma di `AuctionState`/`TakenPick` (entità condivise in
  `entities.py`), semantica di proprietà (owner "Io"), prezzo pagato, derivati
  (budget speso, slot residui da ROSA_SLOTS), JSON versionato, import/export
  bytes.
- `state.py` (layer data): unico modulo che legge/scrive lo stato
  (`data/asta.json`) e fa import/export; mutazioni pure (add_taken con
  duplicati → ValueError, remove_taken); derivati `spent_budget`,
  `slots_remaining(state, players)`, `taken_urls`.
- `tests/test_state.py`: round-trip JSON e bytes su tmp_path, malformed →
  ValueError, mutazioni e derivati.

## Notes

- `data/` è convenienza locale; su Cloud la fonte di verità è il round-trip
  bytes (st.session_state in ui).
- I derivati richiedono i giocatori (ruolo per URL): firma con `players`.

## Resolution

ADR-0004 accettato (modello stato asta). In `entities.py`: `TakenPick`
(url, owner, price) e `AuctionState` (budget, own_team, taken) frozen.
Creato `state.py` (layer data): unico modulo per JSON (`data/asta.json`,
versionato v1), `load_state` (file assente → default), `save_state`,
`export_state`/`import_state` (bytes, malformato → ValueError), mutazioni
pure `add_taken` (duplicato → ValueError) / `remove_taken`, derivati
`taken_urls`, `spent_budget` (solo owner = own_team, None → 0),
`slots_remaining` (ROSA_SLOTS − prese proprie, da `players` per ruolo).

`tests/test_state.py`: 10 test (round-trip JSON e bytes su tmp_path,
malformed → ValueError, mutazioni, derivati). Suite totale 64 test verdi.
