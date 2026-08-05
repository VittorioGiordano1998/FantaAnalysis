# Task: M4-T2 — Limite di spesa per giocatore

- **ID:** M4-T2
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** logic

## Problem

PLANNING §2/§6: per ogni giocatore rimasto serve il prezzo massimo da
offrire all'asta ("punti attesi − costo opportunità"). Senza questo numero
l'app non guida le decisioni durante l'asta.

## Proposed Solution

- `spending_limit(player, players, league, budget, slots, taken_urls,
  price_field) -> SpendingLimit` (ADR-0003):
  - baseline P0: ottimo del pool senza `player` (se `player` è nella rosa
    ottimale di base) o ottimo di base P* (altrimenti);
  - `Q(pr)` = ottimo con `player` forzato in rosa e budget `B − pr`;
  - `max_price` = più grande `pr` intero con `Q(pr) ≥ P0`, via binary
    search monotono (0 se `Q(0) < P0`; B se `Q(B) ≥ P0`).
- `SpendingLimit`: player_url, max_price, baseline_points, forced_points,
  status.
- Prestazioni: ~log2(B) solve per giocatore (~150-300 ms a giocatore,
  cache-data in UI per snapshot); il limite a bulk si appoggia al
  risultato di base (M4-T3).

## Notes

- I forced solve riusano la stessa build del modello M4-T1.
- Forced infeasible → contribuisce −∞ alla ricerca → max_price 0.

## Resolution

`spending_limit(player, players, league, budget, slots, taken_urls,
price_field)` come da ADR-0003: baseline = ottimo senza player (se player
nella rosa di base, un re-solve) o ottimo di base; `Q(pr)` = forced solve
con budget `B − pr` (infeasible → −inf); `max_price` = più grande `pr`
intero con `Q(pr) ≥ baseline` via binary search monotono in [0, B] con
early-exit a 0 e B. `SpendingLimit` con baseline/forced points e status.

Verifica: test esatti sul pool sintetico (selezionato → 445 con
`forced ≥ baseline`; non selezionato → 0; base infeasible → status
Infeasible). E2E reale: Martinez L. (QI 35) → limite 39 crediti
(baseline 1444.0 → forced 1444.4), ~2.4 s per giocatore: usare
on-demand/cachato in UI (M4-T3, M5), non a bulk per interazione.
