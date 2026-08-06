# Task: Guide con alternative complete (rose, candidati, combinazioni)

- **ID:** M8-T5
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** logic | tools

## Problem

Le guide (M8-T4) mostrano solo la rosa ottimale e i top 3 per posizione:
se in asta i top vengono presi da altri non ci sono alternative. L'utente
vuole combinazioni alternative complete.

## Proposed Solution

- `guide.py`:
  - `k_best_rosters(module, players, ..., k=10)`: rosa ottimale + 9
    alternative; l'alternativa n esclude dal pool i titolari delle
    precedenti (piano B, C, ... completi per modulo);
  - `position_candidates(role, players, ...)`: TUTTI i giocatori validi per
    il ruolo (multiruolo incluso), ordinati per copertura → punti → prezzo;
  - `beam_combinations(positions, ..., beam=50, top=50)`: top-50
    combinazioni per riga (beam search) con giornate coperte, punti e costo.
- `tools/generate_guide.py`: stessi 6 file estesi —
  - moduli: foglio Confronto con le 10 alternative per modulo; sezioni
    "Alternativa 1..10" (XI + panchina + metriche);
  - ruoli: lista completa candidati per posizione (senza soglia) + greedy +
    top-50 combinazioni per riga + matrice copertura.
- Test: k-best (esclusione progressiva, limite, Infeasible a pool
  esaurito), candidati completi ordinati, beam determinato con unione
  giornate e senza duplicati.

## Notes

- Nessun ADR: nuove funzioni pure in `guide.py`.

## Resolution

- `guide.py`:
  - `k_best_rosters(module, players, ..., k=10, slots=ROSA_SLOTS)`: rosa
    ottimale + 9 alternative; l'alternativa n esclude dal pool i titolari
    (XI del template) delle precedenti; ferma se il pool si esaurisce o la
    rosa si ripete;
  - `position_candidates(role, players, ...)`: TUTTI i giocatori validi
    (multiruolo incluso), senza soglia, ordinati per copertura → punti →
    prezzo;
  - `beam_combinations(positions, ..., beam=50, top=50)`: top-50
    combinazioni per riga (beam search, niente duplicati, obiettivo
    copertura → punti → costo) → `LineCombination`.
- `tools/generate_guide.py`: opzioni `--alternative` (default 10),
  `--beam` (50), `--top` (50); guide_moduli con foglio Confronto a 40 righe
  (4 moduli × 10 alternative) e sezioni "Alternativa 1..10" (XI +
  panchina + scoperte); guide_ruoli con lista completa candidati per
  posizione, greedy, top combinazioni per riga, matrice copertura.
- 6 test nuovi: esclusione progressiva (XI alt1 ∉ rosa alt2), stop a pool
  esaurito, candidati completi ordinati, multiruolo accettato, beam
  (ranking per copertura con tie-break punti, nessun duplicato).
- Verifica: `pytest` → 130/130; ruff puliti; rigenerazione con dati reali:
  alternative da 500/1493.8 punti (alt 1) a ~325 crediti/660 punti
  (alt 10), tutte con 38/38 giornate coperte; lista POR completa (60
  giocatori) e top combinazioni per riga.
