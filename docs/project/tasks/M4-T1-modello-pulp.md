# Task: M4-T1 — Modello PuLP rosa ottimale

- **ID:** M4-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** logic

## Problem

Manca il cuore dell'app (PLANNING §6): l'ottimizzazione della rosa tra i
giocatori rimasti con budget e slot per ruolo. Senza `optimize.py` non c'è
funzione obiettivo né la base per il limite di spesa (M4-T2).

## Proposed Solution

- ADR-0003 (obbligatorio per RULES: semantica del modello di ottimizzazione)
  con vincoli, obiettivo e formula del limite di spesa.
- `optimize.py` (layer logic, PuLP, puro):
  - `DEFAULT_BUDGET = 500`, `ROSA_SLOTS = {P:2, D:8, C:8, A:7}`;
  - `optimize_squad(players, league, budget, slots, taken_urls,
    price_field)`: massimizza `sum(total_points)` sui soli rimasti, vincolo
    budget ≤, vincoli slot per gruppo = (esatti), prezzo = QI (opzione QA
    con fallback QI);
  - `SquadResult`: selected (tupla ordinata), total_points, total_cost,
    budget, status ("Optimal" | "Infeasible").
  - Pool troppo piccolo o budget insufficiente → status Infeasible (risultato
    esplicito, niente eccezioni).

## Notes

- Variabili PuLP nominate `x_<idx>` (gli URL non sono nomi di variabile
  validi per CBC); mappa url→variabile interna.
- Le proiezioni vengono da `projection.project` (stessa shared truth).

## Resolution

ADR-0003 accettato (semantica ottimizzazione: obiettivo, vincoli, limite
spesa). Creato `optimize.py` (layer logic, PuLP, puro): `DEFAULT_BUDGET=500`,
`ROSA_SLOTS={P:2,D:8,C:8,A:7}`, `optimize_squad(players, league, budget,
slots, taken_urls, price_field)` con variabili binarie `x_<idx>`
(`model.add_variable`, API PuLP 4-ready per la costruzione), vincolo budget
`≤` e slot per gruppo `==`, prezzo QI (QA opzionale con fallback QI, None →
0); `SquadResult` con status esplicito "Optimal"/"Infeasible" (mai
eccezioni). Variabili chiavate per URL. Solver `PULP_CBC_CMD` (bundled;
migrazione PuLP 4.0 → DG-1).

Verifica: 12 test unitari in `tests/test_optimize.py` (pool sintetico
deterministico: ottimo di base, budget che forza scelte più economiche,
presi esclusi, infeasible per pool/budget, price_field QA, ordine rosa,
limite di spesa). E2E su cache reale: solve base 99 ms (target ≤ 1 s),
rosa 2P-8D-8C-7A, costo 500/500, 1493.8 punti attesi.
