# Task: Pagina unica con il listone completo (dati da Listone.xlsx)

- **ID:** M9-T1
- **Status:** Done
- **Date opened:** 2026-08-18
- **Date done:** 2026-08-18
- **Severity:** Medium
- **Area:** ui | data

## Problem

L'utente vuole che il sito mostri UNA sola pagina: il listone completo,
con tutte le informazioni contenute nel file `Listone.xlsx` (ruoli Mantra,
squadra, titolarità, FMV, rigorista, punizioni, angoli, preso da noi/altri).
Lo scraping attuale da Fantacalcio.it non fornisce titolarità, rigorista,
punizioni, angoli né il FMV decimale: il file Excel (generato da FantaLab,
402 giocatori) è la fonte completa scelta dall'utente.

## Proposed Solution

- `resources/listone.xlsx`: copia versionata del file dell'utente (scelta
  dell'utente: file nel repo, funziona anche su Streamlit Cloud; quando lo
  aggiorna, lo ricopia e fa commit). `data/` resta solo cache rigenerabile.
- `entities.py`: nuova entità `ListoneRow` (aggiunta, nessun cambio di forma
  a entità esistenti → nessun ADR richiesto).
- `fetch_listone.py` (layer data): `read_listone(path)` — legge l'Excel e
  mappa le righe su `ListoneRow` (ruoli dalla spunta, titolarità %, FMV,
  flag, presi). File assente → `()` (primo avvio / test).
- `ui_common.py`: `get_listone(force)` cachato (`@st.cache_data`).
- `main.py` riscritta a schermata unica: resta la sidebar (versione,
  aggiorna dati, export/import, report) e il check deploy; il contenuto
  principale diventa il listone con ricerca per nome, filtro squadra e
  filtro gruppo ruolo, tabella completa con tutte le colonne del file.
- Le pagine laterali (`pages/`) restano raggiungibili via URL, invariate.

## Notes

- Nessun ADR: nuova entità display-only, nessuna modifica alle entità
  esistenti né alla semantica di proiezione/ottimizzazione.
- Test: parser su xlsx generato in `tmp_path` (niente disco reale); smoke
  test delle pagine con `LISTONE_PATH` patchato su file assente.

## Resolution

- `resources/listone.xlsx`: copia versionata del file dell'utente
  (352 giocatori reali; le 50 righe vuote in coda al foglio vengono
  escluse dal parser).
- `entities.py`: nuova entità `ListoneRow` (frozen dataclass, display-only:
  nome, squadra, ruoli nell'ordine del file, titolarità, FMV, rigorista,
  punizioni, angoli, preso noi/altri). Nessun ADR: nessuna modifica alle
  entità esistenti né alla semantica di proiezione/ottimizzazione.
- `fetch_listone.py` (layer data): `read_listone(path)` legge l'Excel con
  pandas e mappa le righe su `ListoneRow`; file assente → `()` (primo
  avvio/test). `LISTONE_PATH = resources/listone.xlsx` patchabile nei test.
- `ui_common.py`: `get_listone(force)` con `@st.cache_data` (chiave = flag
  aggiornamento, come gli altri loader).
- `main.py` riscritta a schermata unica: rimosse le sezioni di copertura
  partite facili; resta la sidebar (versione, aggiorna dati, export/import
  stato, report) e il check deploy. Contenuto: listone con ricerca per
  nome, filtro squadra e filtro gruppo ruolo (multiruolo incluso), tabella
  completa con tutte le colonne del file e caption "N giocatori su M".
  Le pagine laterali restano raggiungibili via URL, invariate.
- Test: `tests/test_fetch_listone.py` (4 test su xlsx generato in
  `tmp_path`: mapping completo, ordine multiruolo, righe vuote escluse,
  cella vuota "preso" → False, file assente → vuoto); smoke pages con
  `LISTONE_PATH` patchato + render end-to-end con file in `tmp_path`.
- Verifica: `pytest` → 152/152; `ruff check` e `ruff format --check`
  puliti; render reale AppTest: 352 giocatori su 352, nessuna eccezione.
- Limitazione: se l'utente aggiorna il file Excel, deve ricopiarlo in
  `resources/listone.xlsx` e committare (su Cloud il repo è l'unica
  persistenza).
