# Task: Guide asta — moduli con rosa completa e combinazioni per ruolo

- **ID:** M8-T4
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** logic | tools

## Problem

L'utente vuole due documenti generati dai dati esistenti (proiezioni,
calendario facile, crediti): 1) per ogni modulo, le migliori scelte per la
rosa completa; 2) per ogni ruolo (seguendo i ruoli Mantra di ogni modulo),
le migliori combinazioni per le partite facili. In xlsx, csv e md.

## Proposed Solution

- `guide.py` (logic, puro):
  - `optimize_roster_coverage(players, league, calendar, strengths, budget,
    slots)` → MILP PuLP: rosa completa (2P-8D-8C-7A) tra i rimasti, budget
    vincolo, obiettivo lessicografico copertura giornate facili (peso
    grande) → punti attesi → costo minore; ritorna `CoverageSquad`
    (scelti, punti, costo, giornate coperte, status).
  - `greedy_cover(...)` → presa progressiva: a ogni passo il giocatore che
    aggiunge più giornate facili non coperte (a parità più punti, poi costo
    minore); `top_candidates(...)` → migliori candidati per copertura.
- `tools/generate_guide.py` (CLI): legge la cache `data/` e lo stato asta
  (rimasti = pool, budget residuo), genera in `output/`:
  - `guide_moduli.{xlsx,csv,md}`: per modulo → XI dal template ruoli
    (riuso `formation_positions`) + panchina + costi + copertura +
    confronto;
  - `guide_ruoli.{xlsx,csv,md}`: per modulo → per gruppo → candidati per
    posizione-rolo + greedy cumulativo + matrice copertura gruppo×giornata.
- Test sintetici (nessuna rete): copertura prima dei punti, budget →
    Infeasible, greedy, ranking.

## Notes

- La rosa ottimale è una sola (modulo-indipendente); il modulo definisce
  XI e lettura per ruolo.
- Nessun ADR: nuove funzioni pure in `guide.py`.

## Resolution

- `guide.py` (logic, puro): `optimize_roster_coverage` (MILP PuLP: rosa
  2P-8D-8C-7A tra i rimasti, budget vincolo, obiettivo lessicografico
  copertura giornate facili → punti → costo minore, `CoverageSquad` con
  status Optimal/Infeasible), `greedy_cover` (presa progressiva per
  giornate aggiunte, poi punti, poi costo) e `top_candidates` (ranking per
  copertura). `utility.remaining_weeks` reso pubblico.
- `tools/generate_guide.py` (CLI, `python -m tools.generate_guide`
  [--budget N] [--output DIR]): pool = rimasti dallo stato asta, budget =
  residuo; genera in `output/` (gitignored) `guide_moduli.{xlsx,csv,md}`
  (per modulo: Confronto, XI dal template ruoli con giornate facili,
  panchina, scoperte) e `guide_ruoli.{xlsx,csv,md}` (per modulo per
  gruppo: candidati per posizione, greedy cumulativo, matrice copertura
  gruppo×giornata).
- 7 test sintetici: copertura prima dei punti, budget → Infeasible, slot
  pieni senza pool → Infeasible, greedy (ordine, costi, coperte),
  tie-break punti, ranking candidati.
- Verifica: `pytest` → 124/124; ruff puliti; generazione eseguita con dati
  reali: 494 rimasti, budget 500, ogni modulo → rosa da 500 crediti,
  38/38 giornate coperte, 1493.8 punti, XI coerente coi template.
