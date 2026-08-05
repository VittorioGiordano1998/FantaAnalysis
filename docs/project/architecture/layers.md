# Layer Dependencies

## Allowed direction

```
ui → logic ← data
```

`ui` may call `logic` and `data`. `data` may import types from `logic`. Nothing ever goes the
other way.

## Hard rules

- `logic` (`projection.py`, `optimize.py`) imports nothing first-party except its own modules:
  no `main.py`, no `pages/`, no `fetch_*`, no `state.py`. It does no I/O (no network, no files,
  no `streamlit`) — only computation.
- `ui` (`main.py`, `pages/`) never imports `requests`, `bs4` or `pulp` directly and never writes
  to `data/` or `output/`. It calls `fetch_*`/`state.py` functions and `logic` functions only.
- `data` never imports `streamlit` and never imports `ui`. It maps scraped rows onto `logic`
  entities; raw page/DTO shapes never leak into `ui`.
- `state.py` is the only module that reads/writes the auction-state JSON; `fetch_*` are the only
  modules that hit the network and write the CSV cache.
- Logic semantics (projection model, optimization model, entity shapes) change only via ADR
  (see `docs/agents/RULES.md` §Never change domain logic without an ADR).

## Enforcement

- **CI:** ruff lint/format + pytest on every push/PR (`.github/workflows/ci.yml`).
- **Review checklist:** PRs touching a layer must not import types from a layer below the allowed
  direction, and must not introduce I/O where the layer forbids it. This is a manual read of
  changed imports (see `ROADMAP.md` §Verification).
- A build-time dependency-rule check is wanted but unscheduled; known risk recorded as a
  delivery gap if it becomes live pain.
