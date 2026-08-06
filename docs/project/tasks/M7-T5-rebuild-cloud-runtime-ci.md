# Task: Rebuild Cloud: runtime.txt, CI e redeploy pulito

- **ID:** M7-T5
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Critical
- **Area:** build | docs

## Problem

Dopo i push M7-T2/T3/T4 l'app su Streamlit Cloud va in
`ImportError` a `main.py:31` (`from ui_common import ...`). Il repo su
GitHub è integro (verificato: single branch `main` a `a87cd5a`, file
corretti) e il codice passa 99 test anche con la risoluzione dipendenze
attuale (pandas 3.0.5, PuLP 3.3.2, streamlit 1.61.1). Il traceback a frame
singolo indica un build Cloud stantio/misto o un ambiente diverso
(versione Python non versionata). Inoltre non esiste CI: nessun gate prima
del deploy.

## Proposed Solution

1. `runtime.txt` con `python-3.12`: Streamlit Cloud lo onora, la versione
   Python diventa versionata (non più solo impostazione dashboard).
2. `.github/workflows/ci.yml`: `pytest` + `ruff` su ogni push/PR (Python
   3.12) — nessun codice rotto arriva più su Cloud senza essere visto.
3. DG-2 per la CI mancante e la versione Python non versionata.
4. Redeploy forzato via push (commit con runtime.txt + CI) per scartare
   eventuale cache/clone misto su Cloud; se l'ImportError persiste,
   diagnosi mirata dalla riga `ImportError` nei log Cloud (Manage app →
   Logs).

## Notes

- Il deploy su Cloud ricompila a ogni push su `main`.

## Resolution

- `runtime.txt` → `python-3.12` (versionato; Streamlit Cloud lo onora).
- `.github/workflows/ci.yml`: su ogni push/PR → Python 3.12, `pip install
  -r requirements-dev.txt`, `ruff check .`, `ruff format --check .`,
  `pytest`. La CI esisteva già dal primo commit ma era rossa sui recenti
  push (format check su `fetch_fixtures.py`): riformattati `fetch_fixtures.py`,
  `main.py`, `utility.py`.
- Nuovo `tests/test_smoke_pages.py`: boot delle 3 pagine Streamlit con
  cache vuota e fetch patchati (niente rete, niente disco) — un ImportError
  al boot ora fallisce la CI prima del deploy.
- `DG-2-ci-senza-smoke-test-e-python-non-versionato.md` aggiornato e
  rinominato (la CI esisteva ma non copriva il boot; Python Cloud non era
  versionato).
- Push su `main` = redeploy forzato di Cloud: se l'ImportError persiste
  dopo il rebuild, serve la riga `ImportError` dai log (Manage app → Logs)
  per la diagnosi mirata.
