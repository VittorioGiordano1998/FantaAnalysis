# Task: M7-T1 — Test end-to-end asta simulata

- **ID:** M7-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** test

## Problem

ROADMAP M7: "Test e2e con dati reali: asta simulata dalla presa del primo
giocatore alla rosa finale". Nessun test integra oggi la catena
fixture → entità → stato asta → proiezione → ottimizzazione → limite di
spesa → export/import.

## Proposed Solution

- `tests/test_e2e.py` (senza rete, senza filesystem reale — tmp_path + le
  fixture registrate in `tests/fixtures/`):
  1. costruzione pool reale: listone 2026/27 (494 giocatori) + stats
     2026/27 (a inizio stagione: a zero → stime FVM, comportamento reale
     pre-asta) + calendario settimana 1 (contesto neutro);
  2. rosa ottimale iniziale: 25 giocatori, gruppi 2P-8D-8C-7A, costo ≤ 500;
  3. presa di giocatori da altre squadre → esclusi dall'ottimo successivo;
  4. presa della rosa ottimale per la propria squadra (prezzo = QI) →
     budget speso ≤ 500, slot residui tutti a 0, duplicato → ValueError;
  5. limite di spesa su un giocatore rimasto → status Optimal;
  6. export/import stato round-trip.

## Notes

- Le stats 2026/27 della fixture sono a zero (stagione non iniziata):
  la simulazione replica fedelmente l'uso dell'app prima dell'asta.
- Nessuna rete: tutto da fixture.

## Resolution

Creato `tests/test_e2e.py` (senza rete, tmp_path + fixture registrate):
asta simulata end-to-end su dati reali 2026/27 —

1. pool reale: 494 giocatori (listone) + stats di inizio stagione (a zero:
   stime FVM, comportamento reale pre-asta) + contesto calendario neutro;
2. rosa ottimale iniziale: 25 giocatori, 2P-8D-8C-7A, costo ≤ 500;
3. 3 prese di altre squadre → giocatori esclusi dagli ottimi successivi;
4. limite di spesa su un rimasto → status Optimal, 0 ≤ max ≤ budget;
5. presa dell'intera rosa per la propria squadra (prezzo QI) → spesa
   ≤ 500 e uguale al costo della rosa, slot residui tutti a 0;
6. presa duplicata → ValueError; export/import stato round-trip.

Durata ~3 s. Suite completa: 72 test verdi, ruff pulito.
