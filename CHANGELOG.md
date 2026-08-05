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
