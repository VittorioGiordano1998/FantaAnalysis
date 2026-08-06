# Task: Pagina Guide con rose alternative disegnate come formazioni

- **ID:** M8-T6
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** ui

## Problem

Le guide (M8-T4/T5) sono file tabellari (xlsx/csv/md): l'utente vuole
visualizzare le rose alternative all'interno di formazioni con i rispettivi
moduli, come nella tab Asta.

## Proposed Solution

- `ui_common.py`: helper condivisi `role_codes(roles)` e
  `render_formation(module, players)` (disegna le righe del modulo con
  nomi, squadra, codici multiruolo e flag "Mancano"), estratti da
  `main.py`.
- `main.py`: `_render_formazione` riusa `render_formation`.
- Nuova pagina `pages/Guide.py`: calcola le rose alternative per modulo
  (`k_best_rosters`, cachato per snapshot asta + budget) e le mostra come
  formazioni disegnate: selettori modulo + alternativa, riepilogo
  (costo/coperto/punti/scoperte), panchina in expander; seconda tab
  "Confronto" con la tabella modulo×alternativa.
- Smoke test: la pagina va aggiunta a `tests/test_smoke_pages.py` (con
  cache vuota mostra l'info e non calcola nulla).

## Notes

- Il primo calcolo per snapshot asta è lento (~10 s, 40 solve PuLP), poi
  cachato.
- Nessun ADR: solo UI e riuso di logica esistente.

## Resolution

- `ui_common.py`: `role_codes(roles)` e `render_formation(module, players)`
  condivisi (disegna le righe del modulo: nome, squadra, codici multiruolo,
  "—" con ruolo richiesto e flag "Mancano"), estratti da `main.py`.
- `main.py`: `_render_formazione` riusa `render_formation`; rimossi
  `_role_codes` e gli import non più usati.
- Nuova pagina `pages/Guide.py` (tab "Rose alternative" / "Confronto"):
  - Rose alternative: selettori modulo e alternativa (10), formazione
    disegnata con la rosa scelta, riepilogo costo/coperto/punti, panchina e
    giornate scoperte in expander;
  - Confronto: tabella modulo × alternativa con costo, coperto, punti,
    scoperte;
  - calcolo `k_best_rosters` cachato per snapshot asta + budget (`_rose`).
- `tests/test_smoke_pages.py`: aggiunta `pages/Guide.py` (con cache vuota
  mostra l'info, nessun calcolo).
- Verifica: `pytest` → 131/131; ruff puliti; smoke AppTest con dati reali:
  alt 1 → 500 crediti/1493.8 punti, alt 4 → 436/1038.9 (coerente con i
  file guida), formazione con nomi e placeholder.
