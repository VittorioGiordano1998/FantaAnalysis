# Task: Cache assente al primo avvio su Cloud

- **ID:** M6-T3
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Critical
- **Area:** data | ui

## Problem

Al primo avvio su Streamlit Cloud (o dopo uno sleep: disco effimero) la
directory `data/` non contiene i CSV di cache. Le funzioni di mappatura
`read_players`, `read_season_stats` e `read_league_context` aprono il file
senza verificarlo e l'app va in `FileNotFoundError` alla prima render
(dalla home: `_render_report` → `state_snapshot` → `get_players`), quindi
l'app è inutilizzabile finché l'utente non preme "Aggiorna dati" — che
però non può vedere. Stesso crash in `pages/RosaOttimale.py` e
`pages/Analisi.py`.

## Proposed Solution

- Nel layer `data`, le funzioni di mappatura ritornano risultati vuoti
  quando la cache non esiste (stesso pattern di `load_state` → default e di
  `cache_mtime` → None):
  - `read_players` → `[]`; `read_season_stats` → `{}`;
    `read_league_context` → `LeagueContext` vuoto (log warning, no crash).
- Nel layer `ui`, quando il listone è vuoto le pagine mostrano
  `st.info("... premi 'Aggiorna dati'")` e saltano i widget dipendenti
  (home: stato asta e report; pagine RosaOttimale e Analisi).
- Test unitari per il comportamento cache-assente nei tre moduli `fetch_*`.

## Notes

- Il percorso "Aggiorna dati" (fetch on demand con `force_refresh=True`) già
  scrive le cache: nessuna modifica lì.
- L'aggiornamento del codice su Cloud è automatico al push su `main`.

## Resolution

- `fetch_quotazioni.read_players` → `[]`, `fetch_stats.read_season_stats` → `{}`,
  `fetch_fixtures.read_league_context` → `LeagueContext` vuoto quando la cache
  non esiste (log warning, niente più `FileNotFoundError`).
- `main.py` (stato asta e report), `pages/RosaOttimale.py`, `pages/Analisi.py`:
  con listone vuoto mostrano "Listone non ancora scaricato: premi 'Aggiorna
  dati'." e saltano i widget dipendenti; `_render_quotazioni` gestisce anche un
  frame vuoto.
- 3 nuovi test unitari (cache assente → risultato vuoto) + smoke test
  Streamlit delle 3 pagine con `data/` vuota (niente rete, funzioni fetch
  patched): pagine OK con messaggio info.
- Verifica: `python -m pytest -q` → 75/75 passati; `ruff check .` pulito.
