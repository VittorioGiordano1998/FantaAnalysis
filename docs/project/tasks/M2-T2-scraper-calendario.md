# Task: M2-T2 — Scraper calendario Serie A

- **ID:** M2-T2
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** data

## Problem

L'aggiustamento calendario delle proiezioni (M3) richiede le partite e le
forze in campo delle prossime giornate. Il calendario Fantacalcio.it non ha
una pagina "tutte le giornate": `/serie-a/calendario` mostra una sola
giornata alla volta, navigabile via `/serie-a/calendario/<N>`.

## Proposed Solution

- Nuovo modulo `fetch_fixtures.py` (layer data):
  - `parse_calendar_html(html)` pura: righe da `div.match-pill` (matchweek,
    squadre casa/trasferta da `meta[itemprop=name]` + id team da
    `for="team-N"`, risultato da `span.score-home/away`, data
    `meta[itemprop=startDate]`, ora, stadio, stato `data-match-status`,
    URL match) con **dedup per URL match** (la pagina rende ogni partita
    due volte: una vista per giornata e una raggruppata per data).
  - `get_calendario(force_refresh=False)`: 38 GET (una per giornata,
    `/serie-a/calendario/1..38`, rate-limited a 1s) → merge → cache CSV
    settimanale `data/calendario.csv`.
- Fixture: giornata 1 stagione corrente (con duplicati, per testare il
  dedup) + test senza rete.

## Notes

- La stagione si ricava dall'URL del match (`/calendario/1/2026-27/...`).
- Nessuna pagina calendario della stagione passata è fruibile (il pattern
  `/calendario/1/2025-26` redirige al dettaglio partita): fixture solo su
  stagione corrente, partite non giocate (risultati 0-0, status 0).

## Resolution

Creato `fetch_fixtures.py` (layer data): `parse_calendar_html` pura su
`div.match-pill` (squadre da meta schema.org, id team da `for="team-N"`,
risultato, data/ora/stadio, stato `data-match-status`, URL partita) con
dedup per URL normalizzato al path (la pagina mescola href assoluti e
relativi e rende ogni partita due volte); giornata ricavata dall'URL
(`/calendario/<N>/...`) con fallback al DOM (una pagina servita durante i
test conteneva l'intera stagione con matchweek errato nel DOM).
`get_calendario(force_refresh=False)`: 38 GET rate-limited, dedup globale,
CSV settimanale `data/calendario.csv` (380 partite).

Fixture `calendario_2026_27_week1.html` (slice reale con 20 pill → 10
partite uniche) + `tests/test_fetch_fixtures.py`: 5 test senza rete
(dedup, campi noti Inter-Monza, 20 squadre, round-trip CSV, riuso cache).
Verificato end-to-end: 38 giornate × 10 partite, CSV scritto. CI verde
(ruff + pytest 20/20 complessivi).

Nota: la pagina del calendario stagione passata non è fruibile (redirect al
dettaglio partita); fixture solo su stagione corrente, partite non giocate.
