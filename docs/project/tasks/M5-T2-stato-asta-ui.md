# Task: M5-T2 — Stato asta interattivo in main.py

- **ID:** M5-T2
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** ui

## Problem

PLANNING §2 (#1): a ogni presa all'asta l'utente deve poter segnare il
giocatore (tua squadra o altre) con aggiornamento immediato di budget e
slot. L'app oggi non ha widget per interagire con lo stato.

## Proposed Solution

- `ui_common.py` (layer ui, helper condivisi tra main e pagine):
  `get_players`/`get_league` con `@st.cache_data` (chiave = flag
  aggiornamento), accessor `get_state`/`set_state` su `st.session_state`
  (con persistenza locale via state.py), mappa etichette ruoli italiane.
- `main.py`: card riassuntive (budget residuo, slot per gruppo), widget
  "Prendi giocatore" (ricerca per nome, owner "Io" o altro, prezzo pagato
  solo per "Io"), widget "Annulla presa", tabella delle prese, sezione
  export/import stato (download/upload bytes) — tutto delegando a
  `state.py`/`logic`, niente I/O diretto.

## Notes

- UI non unit-testata (verifica manuale + smoke headless).
- Su Cloud il disco è effimero: l'import/export è il percorso ufficiale,
  `data/asta.json` convenienza locale.

## Resolution

Creato `ui_common.py` (helper ui): `get_players`/`get_league` con
`@st.cache_data` (chiave = flag aggiornamento), accessor
`get_state`/`set_state` su `st.session_state` (persistenza locale via
state.py), `ROLE_LABELS` italiane. `main.py` ristrutturato: pulsante
"Aggiorna dati" (invalidation unica), card budget residuo + slot per
gruppo, widget "Prendi giocatore" (selectbox per nome, owner con prezzo
obbligatorio solo per "Io", duplicati bloccati), "Annulla presa", tabella
delle prese (ordine inverso), export/import stato nella sidebar
(download/upload bytes, errore su file non valido); listone quotazioni
invariato; anteprima rosa M4 spostata in `pages/RosaOttimale.py`.

Verifica: smoke AppTest — presa Martinez (metric 465/500), annulla,
nessuna eccezione; app headless HTTP 200 su main e pagine.
