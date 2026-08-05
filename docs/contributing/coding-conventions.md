# Coding Conventions

Machine-checked by ruff (`ruff check .`, `ruff format --check .`) using `.editorconfig` and
`pyproject.toml`.

## Style

- 4 spaces, LF endings, max line 100.
- `@dataclass(frozen=True)` for entities; pure functions for logic; explicit results over
  exceptions for expected failures.
- Module layout mirrors the layers: `ui` (`main.py`, `pages/`), `logic` (`projection.py`,
  `optimize.py`), `data` (`fetch_*.py`, `state.py`).

## Naming

- Modules/functions/variables: `snake_case`. Classes: `PascalCase`. Constants: `UPPER_SNAKE_CASE`.
- Tests: `test_<subject>.py` in `tests/`; test functions `test_<behaviour>` describing the
  expected outcome.

## Types

- Type hints everywhere; no `Any` where a concrete type exists.
- Prefer `Optional[T]` only where absence is a deliberate contract.
- Public functions: Google-style docstrings (one-line summary + args/returns when non-obvious).

## Logging

Use the `logging` module, logger named per module (`logging.getLogger(__name__)`). No bare
`print()` in production code.

## I/O boundaries

- Network and file I/O live in `data` only. `logic` never reads files, never calls the network,
  never imports `requests`/`bs4`/`streamlit`.
- Scrapers are cache-first and tested against fixtures, never against a live page.

## Streamlit

- `@st.cache_data` on every expensive, input-stable computation (scraped frames, CSV loads,
  optimization results); keys must cover all inputs.
- UI text in Italian; behaviour-defining numbers are `UPPER_SNAKE_CASE` constants in one place.
