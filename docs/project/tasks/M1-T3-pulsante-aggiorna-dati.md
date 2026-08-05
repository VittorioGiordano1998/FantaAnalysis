# Task: M1-T3 — Pulsante "Aggiorna dati" e invalidation cache

- **ID:** M1-T3
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** Medium
- **Area:** ui

## Problem

La cache CSV settimanale deve essere invalidabile esplicitamente: RULES
(§Performance, §UI) richiedono che il pulsante "Aggiorna dati" sia l'unica
via di invalidazione e che i dati stabili siano decorati con `@st.cache_data`.

## Proposed Solution

- `main.py` minimale (M1): tabella quotazioni leggibile da mobile + pulsante
  "Aggiorna dati".
- `@st.cache_data` sul caricamento del CSV, chiave = mtime del file + flag
  force; il pulsante chiama `get_quotazioni(force_refresh=True)` e invalida.
- UI solo rendering: nessuna logica di parsing né I/O diretto nel modulo ui
  (delega a `fetch_quotazioni.get_quotazioni`).

## Notes

- I test unitari non coprono `main.py` (verifica manuale con
  `streamlit run main.py`, da `docs/contributing/testing.md`).

## Resolution

Creato `main.py` minimale: titolo e caption in italiano, pulsante "Aggiorna
dati" che chiama `get_quotazioni(force_refresh=True)` e ribalta il flag di
sessione (unica via di invalidazione), `@st.cache_data` sul caricamento del
CSV chiavato sul flag, tabella compatta (Nome/Squadra/Ruolo/QI/QA/FVM,
`hide_index`, larghezza piena per mobile) con timestamp dell'ultimo
aggiornamento via `cache_mtime()`. UI senza logica di rete/parsing: tutto
delegato a `fetch_quotazioni`.

Verifica manuale non eseguita qui (richiede `streamlit run main.py` su
browser); lint + test unitari verdi.
