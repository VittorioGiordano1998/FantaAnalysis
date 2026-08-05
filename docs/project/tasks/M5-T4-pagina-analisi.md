# Task: M5-T4 — Pagina analisi

- **ID:** M5-T4
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** Medium
- **Area:** ui

## Problem

PLANNING §2 (#4): analisi giocatori — proiezioni punti per ruolo,
calendario facile/difficile delle prossime 5 giornate, top qualità/prezzo.
Manca la pagina.

## Proposed Solution

- `pages/Analisi.py`:
  - tabella dei rimasti con proiezioni (ppm, totale, rapporto
    qualità/prezzo = totale/QI), filtri per gruppo ruolo e squadra,
    ordinabile (compact, mobile);
  - sezione calendario: squadra selezionata → prossimi 5 avversari con
    forza (GF/GA a partita) vs media di lega dal `LeagueContext`;
  - tutto da `logic` (projection) e `ui_common`, nessuna logica inline.

## Notes

- Stesso layout compatto delle altre pagine.

## Resolution

Creato `pages/Analisi.py`: tabella dei rimasti con proiezioni (ppm, punti
stagione, qualità/prezzo = punti/QI), filtri gruppo ruolo e squadra,
ordinamento per Q/P (compact, mobile); sezione calendario: squadra
selezionata → prossimi 5 avversari con gol fatti/subiti a partita e media
di lega (dati assenti → "—" / neutro). Tutto da `logic`/`ui_common`.

Verifica: AppTest — 494 righe, filtro Portieri → 60, calendario Inter → 5
righe, nessuna eccezione.
