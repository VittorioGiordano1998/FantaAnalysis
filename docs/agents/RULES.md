# Rules for Agentic Tooling

This file is the single source of truth for both Claude Code and opencode.

## Naming

- Modules: `snake_case` (`fetch_quotazioni.py`, `projection.py`, `optimize.py`).
- Classes: `PascalCase` (`SquadOptimizer`, `AuctionState`). Functions and variables:
  `snake_case` (`optimize_squad`, `projected_points`). Constants: `UPPER_SNAKE_CASE`
  (`DEFAULT_BUDGET`, `ROSA_SLOTS`).
- Streamlit pages: files under `pages/` named `PascalCase.py` (`pages/Analisi.py`), UI text in
  Italian.
- Interfaces carry no marker prefix; a protocol/abstract base is named after the capability
  (`PlayerSource`, not `IPlayerSource`).

`.editorconfig` encodes what can be machine-checked (ruff). It is the enforcement, this is the why.

## Layers

Allowed dependency direction:

```
ui → logic ← data
```

Never the reverse.

Concretely:

- `ui` (`main.py`, `pages/`) — Streamlit rendering and user input only. It delegates to `logic`
  and `data` functions and **never** does network I/O, never imports `requests`/`bs4` directly,
  and never builds/solves PuLP models inline (that is `optimize.py`'s job).
- `logic` (`projection.py`, `optimize.py`) — pure computation: point projections and squad
  optimization. **No I/O** (no network, no files, no Streamlit). It is the shared truth: both the
  live path (fresh scrape) and the cached path (CSV) converge on its types.
- `data` (`fetch_quotazioni.py`, `fetch_stats.py`, `fetch_fixtures.py`, `state.py`) — every
  network call and every file read/write lives here. `fetch_*` scrape and write the CSV cache in
  `data/`; `state.py` owns the auction-state JSON (read/write + import/export). `data` may import
  types from `logic`; `logic` never imports from `data` or `ui`.
- Shared entities (`Player`, `Quote`, ...) are `@dataclass` defined in `logic`; `data` maps raw
  scraped rows onto them. Raw page/DTO shapes never leak into `ui`.

## External services / configuration

- No hard-coded endpoints, hosts, keys, or client identifiers scattered in the code: source URLs
  and CSS selectors are module-level `UPPER_SNAKE_CASE` constants in the owning `fetch_*` module.
- Every scraper sends a `User-Agent` header identifying the app, respects the source's terms,
  rate-limits between requests, and is **cache-first**: a fresh weekly cache is never refetched.
- Every external source sits behind a `fetch_*` function that can be pointed at saved fixture
  HTML/CSV. No unit test hits the network; no unit test depends on a live page structure.

## Data / persistence

- `fetch_*` write CSV cache only in `data/` (gitignored, regenerable). `state.py` is the only
  module that reads/writes the auction-state JSON; import/export goes through it.
- `output/` holds generated Excel reports (gitignored).
- Streamlit Cloud has no persistent disk: state must round-trip through export/import bytes;
  `data/` is a convenience cache for local runs, never the source of truth for state.

## Task-first workflow

An agent that is asked to do non-trivial work creates the tracking records itself, in this
order, using the templates in `docs/project/`:

1. **Create the task first.** `docs/project/tasks/<Name>.md` from `TASK_TEMPLATE.md` (or
   `/new-task <Name>`). Fill `Problem` and `Proposed Solution` before executing.
2. **Execute the work**, moving the task to `In Progress`.
3. **When done, close the task**: `Status: Done`, `Date done`, and `Resolution` describing what
   changed and how it was verified.
4. **File a Known Issue for anything left broken.** If the work leaves an unresolved problem
   behind (reproduced or confirmed by inspection), create
   `docs/project/known_issues/KI-<N>-<slug>.md` from `KNOWN_ISSUE_TEMPLATE.md` (or
   `/new-issue <Title>`). Link related delivery gaps with a `Related:` line.
5. **Delivery gaps** (missing milestone work, missing CI, config gaps — not defects in a
   completed feature) go in `docs/project/delivery_gap/DG-<N>-<slug>.md` from
   `DELIVERY_GAP_TEMPLATE.md` (or `/new-dg <Title>`).

Records are cheap to create and cheap to close; a problem that is not recorded is a problem that
will be rediscovered. Trivial changes (typos, one-line fixes inside an existing tracked effort)
do not need a task.

## Never change domain logic without an ADR

`logic` is the shared truth. Bug-fix patches and new pure functions are fine; changing the *shape*
of an entity (`Player`, `Quote`, rosa model) or the *semantics* of the projection/optimization
model must go through a separate ADR (`docs/project/architecture/adr/`).

## Performance

Targets: recompute of the optimal squad after an auction change ≤ 1 s; no refetch on every page
interaction.

- Streamlit: decorate expensive, stable computations with `@st.cache_data` (scraped frames, CSV
  loads, optimization results keyed by input snapshot). Cache keys must cover every input.
- The PuLP model is rebuilt only when the input set changes (players/budget/slots); solve once per
  key, reuse cached results.
- Never load the full CSV cache when a projection exists; load lazily per page.
- The "Aggiorna dati" button is the only path that invalidates the cache.

## UI / resources

- UI text is Italian and user-facing strings are written inline where they belong to a page —
  but numbers that define behaviour (budget, roster slots, score weights) live in one place as
  `UPPER_SNAKE_CASE` constants or `st.session_state` defaults, never hard-coded in two spots.
- The app must stay usable on a phone during the auction: compact tables, no huge dataframes in
  the main path.

## Code style

- 4 spaces, LF endings, max line 100, ruff (`py311`) with `E W F I UP B SIM` rulesets.
- Docstrings (Google style) on public modules and functions; type hints everywhere; no `Any`
  where a concrete type exists.
- `@dataclass(frozen=True)` for entities; pure functions for logic; explicit results over
  exceptions for expected failures (empty roster, insolvable budget).
- No `print()` in production code — `logging` only, with the module as logger name.
- Unit tests never touch the network or the real filesystem (use `tmp_path`); scrapers are tested
  against fixtures recorded from real pages.
