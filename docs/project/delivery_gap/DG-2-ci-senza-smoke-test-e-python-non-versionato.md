# Delivery Gap: CI senza smoke test di boot e Python Cloud non versionato

- **ID:** DG-2
- **Status:** Open
- **Release impact:** n/a — risk
- **Date opened:** 2026-08-06

## Description

La CI esiste dal primo commit (`.github/workflows/ci.yml`, pytest + ruff
+ ruff format) ma **non esegue le pagine Streamlit**: un errore al boot
(es. l'ImportError a `main.py:31` su Cloud) passa inosservato finché
l'app non viene aperta in produzione. Inoltre i recenti push (M7-T3/T7-T4)
hanno avuto la CI rossa sul format check (`ruff format --check` su
`fetch_fixtures.py`), bloccando anche lo step pytest.

La versione Python di Cloud era configurata solo nella dashboard
("Advanced settings"), non versionata nel repo: se l'impostazione manca o
regredisce, il codice (es. `StrEnum`, richiesto da Python ≥ 3.11 in
`entities.py`) si rompe a runtime.

Fix direction: smoke test AppTest delle pagine in CI (test_smoke_pages.py,
cache vuota e fetch patchati: niente rete, niente disco) e `runtime.txt`
con `python-3.12` per pinnare la versione Python di Cloud.

## Notes

- Related: M7-T5, DG-1 (la CI è prerequisito della migrazione PuLP 4.0).
