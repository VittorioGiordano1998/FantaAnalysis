# Task: Formazione con posizioni Mantra vincolanti

- **ID:** M8-T2
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** logic | ui

## Problem

La formazione disegnata (M8-T1) riempie le righe del modulo solo per
gruppo ruolo (P/D/C/A), senza vincoli di ruolo Mantra: non segnala se i
propri presi coprono i ruoli specifici (es. 4 difensori = 2 DC + 1 DD +
1 DS). L'utente vuole posizioni Mantra vincolanti con segnalazione dei
ruoli scoperti.

## Proposed Solution

- `utility.py`: `MODULE_POSITIONS` (per ogni modulo, le posizioni con il
  ruolo Mantra richiesto per riga P/D/C/A) e `formation_positions(module,
  own_players)` che assegna i propri presi alle posizioni (ruolo esatto,
  giocatori distinti per posizioni ripetute; posizioni scoperte →
  `player=None`). Sostituisce `FormationLine`/`formation_lines`.
- `main.py` `_render_formazione`: ogni posizione mostra nome, squadra e
  ruolo Mantra (es. "Difensore centrale"); le posizioni scoperte mostrano
  il ruolo mancante evidenziato; caption "Mancano: DD, DS" per riga.
- Test: assegnazione ruoli esatti, posizioni ripetute con giocatori
  distinti, ruoli mancanti → `None`, rosa vuota.

## Notes

- Template ruoli per modulo: 4-3-3 → D dc,dc,dd,ds · C m,c,t · A pc,a,a;
  3-5-2 → D dc,dc,dc · C e,m,c,c,e · A pc,pc; 4-4-2 → D dc,dc,dd,ds ·
  C e,m,c,e · A pc,pc; 3-4-3 → D dc,dc,dc · C e,m,c,e · A a,pc,a.
- Nessun ADR: nuove funzioni pure in `utility.py`.

## Resolution

- `utility.py`: `MODULE_POSITIONS` (template ruoli Mantra per modulo: 4-3-3
  → D dc,dc,dd,ds · C m,c,t · A pc,a,a; 3-5-2 → D dc,dc,dc · C e,m,c,c,e ·
  A pc,pc; 4-4-2 → D dc,dc,dd,ds · C e,m,c,e · A pc,pc; 3-4-3 → D dc,dc,dc
  · C e,m,c,e · A a,pc,a) e `formation_positions(module, own_players)` che
  assegna i propri presi alle posizioni (ruolo esatto, giocatori distinti
  per posizioni ripetute; scoperto → `None`); `missing_roles` elenca i
  ruoli scoperti di una riga. Sostituiti `FormationLine`/`formation_lines`.
- `main.py` `_render_formazione`: ogni posizione mostra nome, squadra e
  ruolo Mantra (ROLE_LABELS); le posizioni scoperte mostrano il ruolo
  mancante; caption "Mancano: ..." per riga; contatori rosa invariati.
- 4 test riscritti/aggiunti: assegnazione ruoli esatti, posizioni ripetute
  con giocatori distinti, ruoli mancanti → `None` + `missing_roles`, rosa
  vuota.
- Verifica: `pytest` → 110/110; `ruff check` + `ruff format --check`
  puliti; smoke test: presa di un PC in 4-3-3 riempie la posizione e
  segnala solo "Mancano: Attaccante, Attaccante"; cambio modulo aggiorna i
  ruoli richiesti.
