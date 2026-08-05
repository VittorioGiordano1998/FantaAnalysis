# ADR: Tech stack and layer rules

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision-makers:** project owner

## Context

The product plan (`PLANNING.md`) requires a web app usable from the phone during the auction
that tracks the auction state and recomputes the optimal squad among remaining players. The
source data (quotazioni Fantacalcio.it, statistiche, calendario, Understat xG) is scraped and
can change weekly; the app has no budget for paid hosting. Two tensions drive the architecture:

1. UI speed: the optimizer must recompute within ~1 s after an auction change, without
   refetching the web every interaction.
2. Testability: scraping depends on external pages that change; optimization and projections
   are pure math and must be testable without network or files.

## Decision

- **UI:** Streamlit (`main.py` + `pages/`), deployed on Streamlit Community Cloud; UI text in
  Italian, layout usable on a phone.
- **Optimization:** PuLP with the objective of maximizing expected points, constraints on
  budget (default 500M), roster slots (2P-8D-8C-7A, configurable) and remaining players only;
  per-player spending limit from projected points minus opportunity cost.
- **Data:** scraping via `requests` + `BeautifulSoup` in three `fetch_*` modules, cache-first
  weekly CSV under `data/`; "Aggiorna dati" invalidates the cache. Auction state lives in a JSON
  file handled exclusively by `state.py`, with byte-based import/export (Streamlit Cloud has no
  persistent disk).
- **Layers:** `ui → logic ← data`, never the reverse. `logic` (`projection.py`, `optimize.py`)
  is pure computation with no I/O and owns the shared entities (`Player`, `Quote`) as
  `@dataclass`. All network/file I/O lives in `data`; `ui` never imports `requests`/`bs4`/`pulp`.
- **Verification on the web:** ruff lint + format and pytest run in GitHub Actions on every
  push/PR; unit tests never hit the network (scrapers tested against recorded fixtures).

## Consequences

- Easier: cheap free hosting; every logic branch unit-testable; cache avoids slow scrapes during
  the auction; CI gives verification without a local toolchain.
- Harder: Streamlit Cloud's ephemeral disk forces the state round-trip through bytes; scrapers
  are brittle by nature and must be pinned by fixtures; manual review is required to keep the
  layer boundaries honest (no automated dependency-rule check yet — see `layers.md` §Enforcement).
- Revisit later: the layer-boundary check, and a possible static typed model if the projection
  logic grows.

## Alternatives considered

- **Native/desktop app:** rejected — requires install, complicates phone use during the auction.
- **Static dataset bundled with the app:** rejected — data changes weekly and the auction runs
  for months; a refresh path is required.
- **No cache (live scrape every page load):** rejected — slow during the auction and abusive to
  the source sites.
- **Excel/Google Sheets as the UI:** rejected — no real-time optimization or analysis without
  significant workaround complexity.
