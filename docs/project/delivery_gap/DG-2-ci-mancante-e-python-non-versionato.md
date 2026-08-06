# Delivery Gap: CI mancante e versione Python non versionata

- **ID:** DG-2
- **Status:** Open
- **Release impact:** n/a — risk
- **Date opened:** 2026-08-06

## Description

Il repo non ha alcuna CI (nessun `.github/workflows`): il deploy su
Streamlit Cloud avviene a ogni push su `main` senza alcun gate. Risultato
concreto: un ImportError al boot è arrivato in produzione (app non
usabile) senza essere intercettato da nessun test — la suite locale (99
test) passava, ma nessuno verificava il codice prima del push.

Inoltre la versione Python di Cloud era configurata solo nella dashboard
("Advanced settings"), non versionata nel repo: se l'impostazione manca o
regredisce, il codice (es. `StrEnum`, richiesto da Python ≥ 3.11 in
`entities.py`) si rompe a runtime.

Fix direction: CI con `pytest` + `ruff` su ogni push (`.github/workflows/
ci.yml`) e `runtime.txt` con `python-3.12` per pinnare la versione Python
anche fuori dalla dashboard.

## Notes

- Related: M7-T5 (rebuild deploy), KI-2 (se aperto).
- DG-1 ha già rilevato che il CI manca come vincolo per la migrazione
  PuLP 4.0: la CI qui aggiunta è il prerequisito.
