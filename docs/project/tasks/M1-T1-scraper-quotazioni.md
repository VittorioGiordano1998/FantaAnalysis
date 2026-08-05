# Task: M1-T1 — Scraper quotazioni + cache CSV

- **ID:** M1-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** data

## Problem

M1 della roadmap: non esiste ancora alcun modulo che legga le quotazioni dal
listone ufficiale Fantacalcio.it (QI, QA, FVM, squadra, ruolo Mantra). Senza
questo dato non può partire né il modello di proiezione né l'ottimizzatore.

## Proposed Solution

Nuovo modulo `fetch_quotazioni.py` (layer `data`):

- GET di `https://www.fantacalcio.it/quotazioni-fantacalcio` con header
  `User-Agent` identificativo dell'app; la pagina rende la tabella server-side
  (paginazione client-side, tutti i 494 giocatori nel DOM).
- Parsing con BeautifulSoup:
  - righe: `#prices tbody tr.player-row`;
  - nome da `data-filter-keywords`, ruolo Mantra da `span.role-mantra`
    (`data-value` + `title`), squadra da `td.player-team` + mappa id→nome
    dal `select#team`;
  - QI/QA/FVM Mantra da `td.player-mantra-*`;
  - URL pagina giocatore dal link in `th.player-name` (riuso futuro per stats).
- Funzione pura `parse_quotazioni_html(html)` (testabile su fixture) +
  scrittura CSV settimanale in `data/quotazioni.csv` (cache-first,
  `CACHE_MAX_AGE_DAYS = 7`).
- `get_quotazioni(force_refresh=False)` come unica porta d'accesso: cache fresh
  → riuso; altrimenti fetch → parse → write → ritorna.

## Notes

- La paginazione è client-side: non serve girare le pagine.
- Stagione attiva (2026/27) letta da `select#season option[selected]` e
  salvata nel CSV.
- Nessun hard-coding di selettori nei moduli ui/logic; tutte le costanti
  `UPPER_SNAKE_CASE` nel modulo proprietario.
- Il test non tocca la rete: fixture HTML registrata in `tests/fixtures/`.

## Resolution

Creato `fetch_quotazioni.py` (layer data): GET della pagina quotazioni con
User-Agent identificativo (`USER_AGENT`), parsing puro
`parse_quotazioni_html` su `#prices tbody tr.player-row` con selettori
`UPPER_SNAKE_CASE` di modulo, mappa squadre da `select#team`, stagione da
`select#season`, prezzi interi da `td.player-mantra-*`, URL pagina giocatore
per il futuro `fetch_stats`. Cache-first settimanale:
`get_quotazioni(force_refresh=False)` riusa `data/quotazioni.csv` se fresco
(7 giorni, `CACHE_MAX_AGE_DAYS`), altrimenti fetch → parse → write; porta
d'accesso unica con DataFrame pandas (csv utf-8-sig, leggibile da Excel).

Verificato end-to-end con fetch reale: 494 giocatori, 20 squadre, 12 ruoli
Mantra, CSV scritto in `data/quotazioni.csv`. CI verde (ruff lint/format,
pytest 8/8).
