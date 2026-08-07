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

### Changed

- `pyproject.toml`: `pythonpath = ["."]` per l'import dei moduli nei test.
