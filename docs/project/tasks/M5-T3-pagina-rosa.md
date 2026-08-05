# Task: M5-T3 — Pagina rosa ottimale + limite di spesa

- **ID:** M5-T3
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** ui

## Problem

PLANNING §2 (#2, #3): la rosa ottimale tra i rimasti deve riflettere lo
stato asta (presi, budget residuo, slot residui) e mostrare il prezzo
massimo consigliato per il giocatore in asta. L'anteprima M4 in main.py non
usa lo stato e il limite non è esposto.

## Proposed Solution

- `pages/RosaOttimale.py`:
  - rosa ottimale con `@st.cache_data` chiavata su (prese, budget, slot
    residui, flag): chiama `optimize_squad` con budget residuo e slot
    rimanenti (i miei slot già occupati sono tolti);
  - tabella compatta con punti attesi per giocatore + totali;
  - limite di spesa: ricerca giocatore rimasto → `spending_limit`
    (on-demand, ~2-3 s, spinner + cache per snapshot);
  - Infeasible → avviso chiaro.
- Rimozione dell'anteprima M4 da main.py (spostata qui).

## Notes

- Costo del limite ~2.4 s: mai a bulk per interazione, solo su richiesta.

## Resolution

Creato `pages/RosaOttimale.py`: rosa ottimale con `@st.cache_data` chiavata
su (prese, budget residuo, slot residui, flag) — `optimize_squad` con slot
residui (i miei slot già occupati tolti); tabella con punti attesi per
giocatore e totali; Infeasible → warning. Limite di spesa on-demand:
selectbox giocatore rimasto → `spending_limit` (~1.3 s in AppTest, cachato
per snapshot) con messaggio "offri al massimo N crediti" + confronto
baseline/forced. Anteprima M4 rimossa da main.py.

Verifica: AppTest — rosa 25 righe, limite Martinez 39 crediti (baseline
1444.0 → forced 1444.4), nessuna eccezione.
