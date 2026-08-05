# Architecture Overview

FantaOptimizer is a Streamlit web app for the Fantacalcio **Serie A 2026/27** auction
(asta 500M, regolamento **Mantra**, listone ufficiale Fantacalcio.it). It tracks the auction
state — players taken, budget spent, slots left per role — and recomputes in real time the
**optimal squad** among the remaining players with a PuLP optimizer, plus a recommended
**spending limit** per player. Player data (quotazioni, statistics, fixtures) is scraped from
Fantacalcio.it and Understat, cached weekly in CSV under `data/`. The auction state persists as
JSON (with import/export, since Streamlit Cloud has no persistent disk).

## Layer diagram

```
┌─────────────────────────────────────────────────────┐
│              ui  (Streamlit)                         │
│   main.py · pages/*.py                               │
│   stato asta · rosa ottimale · analisi · export      │
└─────────────────────────┬───────────────────────────┘
                          │ chiama funzioni di logic/data
                          │ (mai network / PuLP inline)
┌─────────────────────────▼───────────────────────────┐
│        logic  (pure computation — shared truth)      │
│   projection.py · optimize.py                        │
│   Player · Quote · proiezioni · rosa 2P-8D-8C-7A     │
└─────────────────────────▲───────────────────────────┘
                          │ importa i tipi condivisi
┌─────────────────────────┴───────────────────────────┐
│        data  (tutto l'I/O)                           │
│   fetch_quotazioni.py · fetch_stats.py               │
│   fetch_fixtures.py · state.py                       │
│   CSV cache in data/ · JSON stato asta               │
└─────────────────────────────────────────────────────┘
```

## Layer responsibilities

- **`ui`** — Streamlit rendering and input. Renders auction state, optimal squad, analyses;
  dispatches user actions to `logic`/`data` functions. Never does network I/O and never touches
  `requests`/`bs4`/PuLP directly.
- **`logic`** — pure computation: point projections per Mantra role and squad optimization with
  budget + slot constraints. **No I/O**; the shared truth both the live path and the cached path
  converge on. Entity shapes here (`Player`, `Quote`, rosa model) change only via ADR.
- **`data`** — every network call and every file read/write. `fetch_*` scrape and write the CSV
  cache (weekly, cache-first); `state.py` owns the auction-state JSON and its import/export.

## Key decisions

1. **Streamlit for UI.** One Python codebase, usable from the phone during the auction; free
   hosting on Streamlit Community Cloud.
2. **Cache-first scraping.** Sources are scraped weekly into `data/` CSVs; the "Aggiorna dati"
   button is the only invalidation path. No refetch on every page load.
3. **PuLP for optimization.** The solver is rebuilt only when the input set changes and results
   are cached per input snapshot (`@st.cache_data`) — recompute target ≤ 1 s.
4. **State round-trips through bytes.** Because Streamlit Cloud has no persistent disk, the
   auction state is exportable/importable; `data/` is a local convenience, never the source of
   truth for state.

See [`layers.md`](layers.md) for the hard dependency rules and their enforcement.
