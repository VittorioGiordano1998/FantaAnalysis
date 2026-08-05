# Task: M4-T3 — Caching e prestazioni

- **ID:** M4-T3
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** Medium
- **Area:** ui

## Problem

RULES §Performance: il ricalcolo della rosa dopo una modifica all'asta deve
essere ≤ 1 s e il modello PuLP va ricostruito solo quando cambia l'input
(giocatori/budget/slot). Il limite di spesa a bulk costa ~10-15 s: va
cachato.

## Proposed Solution

- Anteprima "Rosa ottimale" in `main.py` (M4): `@st.cache_data` sulla
  funzione che carica players/stats/contesto e risolve (chiave = snapshot
  input: flag aggiornamento + parametri default).
- Il pulsante "Aggiorna dati" invalida anche questo cache (flag di sessione
  già esistente).
- Nota: il key completo con stato asta (giocatori presi, budget, slot)
  arriva a M5 con `state.py`; la struttura cache è già quella giusta.

## Notes

- `@st.cache_data` vive in ui; `optimize.py` resta puro (niente import
  streamlit in logic).

## Resolution

In `main.py`: `_load_rosa(force)` decorata con `@st.cache_data` (chiave =
flag aggiornamento; a M5 la chiave si estende a stato asta/budget/slot) e
sezione "Rosa ottimale" con tabella compatta (Nome/Sq/Ruolo/Prezzo),
punti attesi e costo; stato Infeasible mostrato con warning. Il pulsante
"Aggiorna dati" invalida anche questo cache (stesso flag di sessione).
`optimize.py` resta puro (nessun import streamlit in logic).

Performance misurata: solve base 99 ms (target ≤ 1 s); limite di spesa
~2.4 s a giocatore → destinato a chiamate on-demand cachate. Suite totale:
54 test verdi, ruff pulito.
