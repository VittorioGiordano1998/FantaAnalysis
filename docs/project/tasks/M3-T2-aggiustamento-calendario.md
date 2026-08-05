# Task: M3-T2 — Aggiustamento calendario su 5 giornate

- **ID:** M3-T2
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** logic

## Problem

PLANNING §5 richiede che la proiezione tenga conto della forza degli
avversari nelle prossime 5 giornate (calendario facile/difficile). Non
esiste una fonte classifica; la forza squadra va derivata dai risultati già
giocati presenti nel calendario (fonte già verificata in M2).

## Proposed Solution

- `LeagueContext` in `logic` (projection.py): stagione, giornata corrente,
  contesto squadra (gol fatti/subiti a partita, prossimi 5 avversari),
  medie di lega.
- `calendar_multiplier(player, league)`: ruolo attaccante/centrocampista
  penalizzato dalla difesa avversaria forte (media GF), difensori/portieri
  penalizzati dall'attacco avversario (media GF); α = 0.5, cap ±10%.
- La forza squadra viene dai match giocati del calendario CSV (status ≠ 0):
  a inizio stagione non ci sono risultati → moltiplicatore neutro 1.0.
- Costruzione del contesto nel layer data (`fetch_fixtures`): lettura CSV →
  `LeagueContext` (M3-T3).

## Notes

- Nessun nuovo scraper (classifica/xG rimandati; Understat già pianificata
  solo come cross-check).
- La giornata corrente = max giornata giocata + 1 (1 se nessuna giocata).

## Resolution

Creati in `projection.py`: `TeamContext` (forze GF/GA a partita, prossimi 5
avversari) e `LeagueContext` (stagione, giornata corrente, medie di lega).
`calendar_multiplier`: attaccanti/centrocampisti crescono con la debolezza
della difesa avversaria (media GA), difensori/portieri con la debolezza
dell'attacco (media GF), α=0.5, clamp ±10%; neutro (1.0) senza risultati
giocati. Il moltiplicatore si applica alle sole prossime 5 giornate nel
totale (`project`). Forza squadra derivata dai match giocati del calendario
CSV (status ≠ 0): nessun nuovo scraper. Test in `tests/test_projection.py`
(moltiplicatore per gruppo ruolo, cap, neutralità) e
`tests/test_fetch_fixtures.py` (contesto da CSV sintetico con risultati).
