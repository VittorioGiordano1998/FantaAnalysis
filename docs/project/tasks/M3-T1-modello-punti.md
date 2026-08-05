# Task: M3-T1 — Tipi condivisi e modello punti per ruolo

- **ID:** M3-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** logic

## Problem

`logic` è la shared truth ma non esiste ancora: mancano le entità condivise
(`Player`, `Quote`, stats) e il modello di proiezione punti per ruolo Mantra
(PLANNING §5). Senza di esso M4 (ottimizzatore) non ha funzione obiettivo.

## Proposed Solution

- ADR-0002 (obbligatorio per RULES: cambia la forma delle entità e la
  semantica della proiezione) con:
  - forme di `Player`, `Quote`, `SeasonStats`, `Role`/`RoleGroup`,
    `LeagueContext`, `PlayerProjection`;
  - formule di proiezione: punti/partita (FM se ≥3 partite, blend se 1-2,
    stima FVM/100 altrimenti), stima partite giocate (proxy da
    `played_matches`, i minuti non esistono — KI-1), aggiustamento
    calendario sulle prossime 5 giornate;
  - costanti comportamentali (38 giornate, 5 settimane, α=0.5, cap ±10%).
- `entities.py`: dataclass frozen + enum ruoli/gruppi (por, dc, b, dd, ds →
  D; e, m, c, w, t → C; a, pc → A; por → P) + `attach_stats` pura.
- `projection.py`: funzioni pure `points_per_match`, `playing_share`,
  `expected_remaining_matches`, `calendar_multiplier`, `project`.

## Notes

- `logic` senza I/O: nessuna lettura CSV; i dati arrivano come tipi.
- I mapper CSV→tipi vivono nel layer data (M3-T3).

## Resolution

ADR-0002 accettato (forme entità + semantica proiezione, come da RULES per
la modifica di logic). Creati:

- `entities.py` (logic): `Role` (StrEnum, 12 codici Mantra), `RoleGroup`
  (P/D/C/A) con `ROLE_GROUP`, `Quote` (qi/qa/fvm), `SeasonStats`,
  `Player` (name, role, team_id/code/name, quote, url, stats) — tutti
  frozen; `attach_stats` puro per il merge delle stats.
- `projection.py` (logic): `points_per_match` (FM se ≥3 partite, blend se
  1-2, FVM/100 altrimenti), `playing_share` (proxy da played_matches,
  KI-1), `expected_remaining_matches`, `calendar_multiplier` e `project`
  con le costanti ADR (`SEASON_MATCHWEEKS=38`, `NEXT_WEEKS=5`,
  `MIN_MATCHES_FOR_STATS=3`, `FVM_PPM_DIVISOR=100`, `CALENDAR_ALPHA=0.5`,
  `CALENDAR_CAP=0.10`).

Nessun I/O in logic. Test unitari puri in `tests/test_projection.py`.
