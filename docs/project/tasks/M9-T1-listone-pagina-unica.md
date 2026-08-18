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

## Follow-up (a tutto schermo, colori dalle regole del file)

- `main.py`: rimosse sidebar, titolo, caption e filtri — resta solo la
  tabella del listone a tutto schermo (`layout="wide"`,
  `height="stretch"`, CSS che nasconde header/toolbar/footer di
  Streamlit).
- Copiate le regole di formattazione condizionale del file Excel
  (Foglio1): riga presa da noi → verde `#B7E1CD`, presa da altri → rosso
  `#E06666`; titolarità 95/75/50/25 → `#93C47D`/`#FFD966`/`#E69138`/
  `#E06666`; FMV ≥ 6 → `#93C47D`, < 6 → `#E06666`. Stesso ordine di
  priorità di Excel: le regole di cella vincono sul colore di riga nelle
  loro colonne (pandas `Styler`).
- Rimosse sidebar, titolo e caption; resta il check deploy (invisibile nel
  funzionamento normale: protegge da deploy misti, `test_deploy_check.py`).
- Verifica: `pytest` → 153/153; ruff puliti; render AppTest su file
  reale senza eccezioni; Styler verificato su righe simulate (preso da
  noi → verde, da altri → rosso).

## Follow-up 2 (bottoni di presa + tabella fino in fondo)

- Le colonne "preso noi"/"preso altri" sono sostituite dai pulsanti
  "Preso da noi" / "Preso da altri" nella toolbar in alto: si selezionano
  una o più righe della tabella (`on_select="rerun"`,
  `selection_mode="multi-row"`) e si preme il pulsante per segnare la
  presa; ripremendo si libera (toggle).
- Stato persistito in `data/listone_flags.json` — `state.py` ora ha
  `LISTONE_FLAGS_FILE` + `load_listone_flags`/`save_listone_flags`
  (mappa nome giocatore → "noi" | "altri" | ""); i flag del file Excel
  restano la base (`_merged_flag`: sessione prima, poi Excel).
- Tabella a tutto schermo fino in fondo: CSS su
  `[data-testid="stDataFrameResizable"]` (height 100vh − toolbar).
- Test: `test_state.py` +4 (round-trip, file assente, valori invalidi,
  file corrotto); `test_smoke_pages.py` bottoni presenti + click senza
  crash + unit di `_merged_flag`/`_toggle_flags`.
- Verifica: `pytest` → 160/160; ruff puliti; render reale: 352 righe, 2
  bottoni, colonna "stato" nascosta, colori su righe simulate.

## Follow-up 3 (prezzo pagato + budget residuo)

- `data/listone_flags.json` passa al formato v2: `{"version": 2,
  "budget": int, "flags": {...}, "prices": {...}}`; `load_listone_flags`
  migra il v1 (mappa piatta) con budget di default e `save_listone_flags`
  scrive l'envelope; nuova entità `ListoneState` in `entities.py`
  (frozen: budget, flags, prices) e funzioni pure
  `listone_spent`/`listone_remaining` in `state.py` (solo presi "noi"
  con prezzo; i prezzi stantii di giocatori liberati non contano).
- `main.py`: toolbar a due righe — prezzo pagato (number_input, si
  azzera dopo il mark via re-mount della chiave) e budget totale
  modificabile (default 500, persistito); caption "Residuo: X / Y
  crediti" (rosso se sopra budget); colonna "Prezzo" nella tabella per
  i presi da noi. `_toggle_flags` ora è pura su `ListoneState`: "noi"
  con prezzo registra il prezzo, liberando o passando ad "altri" il
  prezzo viene rimosso.
- Test: `test_state.py` migrazione v1→v2, round-trip con budget/prezzi,
  valori invalidi scartati, `listone_spent`/`listone_remaining` e prezzi
  stantii; `test_smoke_pages.py` toggle con prezzo/rilascio/budget,
  click senza crash.
- Verifica: `pytest` → 165/165; ruff puliti; render reale: 2 bottoni, 2
  number_input, caption "Residuo: 500 / 500 crediti", colonna prezzo,
  352 righe, nessuna eccezione.

## Follow-up 4 (priorità su rigorista/punizioni/angoli)

- File `resources/listone.xlsx` aggiornato dall'utente: le colonne
  Rigorista/Punizioni/Angoli ora sono una scala di priorità numerica
  (1 = primo tiratore/battitore, 2 = secondo, 3 = terzo) al posto della
  spunta "✔".
- `entities.ListoneRow`: `rigorista`/`punizioni`/`angoli` passano da
  `bool` a `int | None`; `fetch_listone._optional_int` legge la priorità
  (la spunta "✔" residua, es. Miranda J. sugli angoli, vale 1).
- `main.py`: le tre colonne mostrano il numero di priorità
  (`NumberColumn`), niente più spunte.
- Verifica: parser su file reale — 351 giocatori, 58 rigoristi e 58
  battitori d'angolo con priorità 1-3, punizioni 1-2, Miranda J. → angoli
  1; `pytest` → 167/167; ruff puliti; render reale senza eccezioni.
