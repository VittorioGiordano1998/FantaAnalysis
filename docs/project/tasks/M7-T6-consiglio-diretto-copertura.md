# Task: Consiglio diretto di copertura delle giornate scoperte

- **ID:** M7-T6
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** logic | ui

## Problem

La ricerca inversa (M7-T4) richiede di selezionare giornata e ruolo a
mano. L'utente vuole un consiglio diretto e automatico: quale giocatore
rimasto coprirebbe le giornate difficili rimaste, senza input.

## Proposed Solution

- `utility.py`, nuove funzioni pure:
  - `coverage_suggestions(own_players, remaining_players, ...)` → per ogni
    giornata scoperta (presenti senza partite facili) il miglior candidato
    rimasto con partita facile, per punti attesi;
  - `coverage_recommendations(own_players, remaining_players, ..., limit)`
    → classifica dei rimasti per giornate target coperte, poi punti attesi.
    Target: le giornate scoperte della propria rosa; se non ce ne sono
    (rosa vuota o sempre coperta) tutte le giornate rimanenti (il consiglio
    funziona anche pre-asta).
- `main.py` sezione "Copertura giornate facili": blocco "Consiglio diretto"
  (top giocatori con le giornate che coprono) + tabella "Chi copre le
  giornate scoperte" (per ogni giornata scoperta il miglior candidato).
  Calcolo cachato (`_coverage_advice`, chiave = prese + squadra + refresh).
- Test: scelta del candidato migliore per giornata, ranking per copertura,
  fallback a rosa vuota, giornate senza candidati saltate.

## Notes

- Si costruisce su M7-T3/T7-T4 (TeamCalendar, week_coverage, easy_candidates).
- Nessun ADR: nuove funzioni pure in `utility.py`.

## Resolution

- `utility.py`: `WeekSuggestion` e `CoverageRecommendation`; nuove funzioni
  pure `coverage_suggestions` (per ogni giornata scoperta il miglior
  candidato rimasto per punti attesi, senza candidati → saltata) e
  `coverage_recommendations` (ranking per giornate target coperte, poi
  punti attesi; target = giornate scoperte, altrimenti tutte le rimanenti
  via nuovo helper `_remaining_weeks` — il consiglio funziona anche con
  rosa vuota, pre-asta).
- `main.py`: sezione "Copertura giornate facili" → blocco "Consiglio
  diretto" (top 3 con giornate coperte, compatte via `_fmt_weeks`) +
  tabella "Chi copre le giornate scoperte"; calcolo cachato
  (`_coverage_advice`, chiave = prese + squadra + refresh); caption
  esplicita quando la rosa non ha giornate scoperte.
- 4 nuovi test: miglior candidato per giornata, nessuna giornata scoperta
  → vuoto, ranking per copertura, fallback a rosa vuota su tutte le
  giornate.
- Verifica: `pytest` → 106/106; `ruff check` + `ruff format --check`
  puliti; smoke test con dati reali (rosa vuota): Martinez L. copre le
  giornate 1, 2, 4, 6, 7, 9… (140.6 punti), poi Malen e Thuram.
