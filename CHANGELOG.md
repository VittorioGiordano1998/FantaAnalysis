# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Project scaffolding: Streamlit web app skeleton per `PLANNING.md` (layers `ui → logic ← data`),
  with `main.py`, `fetch_quotazioni.py`, `fetch_stats.py`, `fetch_fixtures.py`, `projection.py`,
  `optimize.py` and `state.py` as the target module layout.
- Governance: `.editorconfig`, `CONTRIBUTING.md`, `CHANGELOG.md`, `docs/agents/RULES.md` and the
  task-first workflow with `TASK_TEMPLATE.md`, `KNOWN_ISSUE_TEMPLATE.md` and
  `DELIVERY_GAP_TEMPLATE.md`; `/new-page`, `/new-task`, `/new-issue` and `/new-dg` slash
  commands.
- GitHub PR template and CI workflow (ruff lint + format check + pytest) — verification runs on
  the web (GitHub Actions), no local toolchain required.
- `requirements.txt` (streamlit, pandas, openpyxl, pulp, requests, beautifulsoup4, plotly) and
  `requirements-dev.txt` (ruff, pytest).
- ADR-0001: tech stack and layer rules (Streamlit + PuLP, CSV cache, no network in tests).
- Scrapers with weekly CSV cache and offline fixtures: `fetch_quotazioni.py` (QI/QA/FVM, ruolo
  Mantra, 494 giocatori), `fetch_stats.py` (PV/MV/FM/gol/assist/cartellini/rigori),
  `fetch_fixtures.py` (calendario 38 giornate con dedup); helper condivisi in `fetch_common.py`.
- Shared entities and projection model (`entities.py`, `projection.py`, ADR-0002): punti
  attesi per ruolo Mantra con stima FVM, aggiustamento calendario sulle prossime 5 giornate;
  mapper CSV→entità nel layer data.
- Squad optimizer (`optimize.py`, ADR-0003): rosa 2P-8D-8C-7A con budget (PuLP, solve ~100 ms)
  e limite di spesa per giocatore (binary search su forced solve).
- Live auction state (`state.py`, ADR-0004): JSON locale + export/import bytes (Streamlit
  Cloud), prese con owner e prezzo, budget/slot residui.
- Streamlit UI: home con stato asta interattivo e listone quotazioni, `pages/RosaOttimale.py`
  (rosa ottimale + limite di spesa on-demand), `pages/Analisi.py` (proiezioni,
  qualità/prezzo, calendario); report Excel (`export_excel.py`) con 5 fogli.
- Known issues e delivery gap: KI-1 (minuti giocati non esposti da Fantacalcio.it),
  DG-1 (migrazione PuLP 4.0 / CBC esterno).
- Test end-to-end (`tests/test_e2e.py`): asta simulata con dati reali dalle fixture,
  dalla prima presa alla rosa finale (stato → proiezione → ottimizzazione → limite di
  spesa → export/import).
- Nuova pagina `pages/GuidaAsta.py` (M8-T9): guida asta per squadra in stile FantaLab —
  selettore squadra e rosa completa raggruppata per gruppo ruolo con QI/QA/FVM, media
  voto, presenze e stato all'asta (libero/preso).
- Pagina unica "Listone" (M9-T1): `main.py` mostra il listone completo con tutte le
  informazioni del file `resources/listone.xlsx` (ruoli Mantra, squadra, titolarità,
  FMV, rigorista, punizioni, angoli, preso da noi/altri) con ricerca per nome e filtri
  squadra/gruppo ruolo; nuovo modulo data `fetch_listone.py` (parsing Excel → entità
  `ListoneRow`, righe vuote escluse).
- Listone a tutto schermo (seguito M9-T1): rimossi sidebar, titolo e filtri — `main.py`
  mostra solo la tabella full-screen con le regole di colore copiate dal file Excel
  (riga presa da noi = verde, presa da altri = rosso; titolarità 95/75/50/25 =
  verde/giallo/arancio/rosso; FMV ≥ 6 = verde, < 6 = rosso).
- Bottoni di presa nel listone (seguito M9-T1): le colonne "preso noi/altri" sono
  sostituite dai pulsanti "Preso da noi"/"Preso da altri" — si selezionano una o più
  righe della tabella e si preme il pulsante per segnare la presa (alternato:
  ripremendo si libera). Stato persistito in `data/listone_flags.json` via `state.py`
  (`load_listone_flags`/`save_listone_flags`), i flag del file Excel restano la base;
  tabella a tutto schermo fino in fondo (CSS su `stDataFrameResizable`).
- Prezzo pagato e budget residuo nel listone (seguito M9-T1): campo "Prezzo pagato"
  nella toolbar (applicato ai selezionati, si azzera dopo il mark), campo "Budget
  totale" modificabile (default 500) e caption "Residuo: X / Y crediti" (rosso se si
  è sopra budget). `data/listone_flags.json` passa al formato v2 (budget, flag,
  prezzi) con migrazione automatica dal v1; nuova entità `ListoneState` e funzioni
  `listone_spent`/`listone_remaining` in `state.py`; colonna "Prezzo" nella tabella
  per i presi da noi. Avvisi se si preme un pulsante senza selezione o se si segna
  "Preso da noi" senza prezzo (il mark non viene applicato).
- Scala di priorità sulle specialità (seguito M9-T1): il file `resources/listone.xlsx`
  aggiornato usa numeri (1, 2, 3 = primo/secondo/terzo tiratore o battitore) per
  rigorista, punizioni e angoli; le colonne mostrano la priorità numerica (la vecchia
  spunta "✔" residua viene letta come priorità 3); senza priorità la cella resta vuota
  (nessuno 0).
- Fix deploy misto (seguito M9-T1): Streamlit Cloud poteva servire `main.py` nuovo con
  `fetch_listone.py` vecchio (colonne "True"/"False" al posto di 1/2/3). `_priority`
  ora è tollerante ai bool (True → 1, False → vuoto) e il check deploy verifica anche
  `fetch_listone.LISTONE_PARSER_VERSION` (schema atteso 2); `LOGIC_VERSION` e
  `version.txt` allineati a 0.14.0.
- Verifica integrità listone (seguito M9-T1): `deploy_ok` confronta anche l'hash
  SHA-256 del file `resources/listone.xlsx` servito con `LISTONE_FILE_SHA256`
  (costante in `fetch_listone.py`, da aggiornare a ogni copia del file) — un deploy
  con il listone stantio (es. giocatori rimossi/aggiunti) mostra l'errore "Deploy
  misto". Versione visibile nella toolbar (v0.15.0); `LOGIC_VERSION`/`version.txt` →
  0.15.0.
- Mega listone su stack Sphynx (`web/`, M10-T1, ADR-0006): nuova app Next.js 16 +
  React 19 + TypeScript + Tailwind 4 in `web/` (branch `web/`) con `output: 'export'`,
  tema scuro Sphynx (palette `.dark` da `globals.css`), tabella dati con badge/dot
  stato, chip priorità (rigorista/punizioni/angoli), prese noi/altri con prezzo e
  budget residuo, filtri nome/squadra/gruppo ruolo, export/import dello stato
  (local-first, `localStorage`). Fonte dati `web/src/data/listone.json` versionato,
  generato da `Listone.xlsx` con `tools/convert_listone.py` (stesso schema di
  `fetch_listone.read_listone`). Test logic portati in Vitest
  (`web/test/listone-state.test.ts`) e test del convertitore in pytest
  (`tests/test_convert_listone.py`); CI: job `web` aggiunto a `ci.yml`. Deploy:
  Vercel sul ramo `web/` (azione manuale utente).

### Changed

- `pyproject.toml`: `pythonpath = ["."]` per l'import dei moduli nei test.
