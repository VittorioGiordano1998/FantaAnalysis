# Task: M3-T3 — Mapper data→logic e test unitari

- **ID:** M3-T3
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** data

## Problem

Le entità condivise di `logic` (M3-T1) devono essere popolate dai CSV di
cache (layer data, che può importare i tipi da logic). Senza mapper e test
la proiezione non è consumabile e la matematica non è verificata.

## Proposed Solution

- `fetch_quotazioni.read_players(cache_dir=None) -> list[Player]` (+ colonna
  `team_id` nel CSV quotazioni, necessario per il join con il calendario).
- `fetch_stats.read_season_stats(cache_dir=None) -> dict[str, SeasonStats]`
  chiavato su `player_url`.
- `entities.attach_stats(players, stats_by_url)` per il merge.
- `fetch_fixtures.read_league_context(cache_dir=None) -> LeagueContext`:
  giornata corrente, forze squadra dai match giocati, prossimi 5 avversari.
- Test unitari senza rete: `tests/test_projection.py` (formule pure con
  fixture in-memory) + test mapper nei file `test_fetch_*` esistenti
  (CSV su `tmp_path`).

## Notes

- Nessun test tocca la rete o il filesystem reale (tmp_path).
- Il cambiamento schema CSV quotazioni (+team_id) non richiede migrazione:
  cache rigenerabile.

## Resolution

Mapper nel layer data (data → tipi logic):

- `fetch_quotazioni.read_players` → `list[Player]`; aggiunta colonna
  `team_id` al CSV quotazioni (join col calendario), cache rigenerata.
- `fetch_stats.read_season_stats` → `dict[url, SeasonStats]`.
- `fetch_fixtures.read_league_context` → `LeagueContext` (giornata corrente
  = max giocata + 1; forze GF/GA; prossimi 5 avversari; medie di lega).
- `entities.attach_stats` per il merge.

Test senza rete: `tests/test_projection.py` (17 test formule pure con
fixture in-memory) + 3 test mapper nei file `test_fetch_*` (CSV su
tmp_path). Totale suite: 42 test verdi, ruff lint/format puliti. Sanity e2e
con cache reale: 494 giocatori proiettati, contesto 20 squadre, moltiplicatore
neutro a inizio stagione (nessun risultato), top proiezioni = Martinez/Malen/
Thuram con ~3.7/3.65/2.8 ppm come atteso da FVM.
