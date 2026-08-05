# Contributing to FantaOptimizer

Thank you for contributing. This document is the single source of truth for how we work.

## Quick reference

- **Branching:** Trunk-based + short feature branches (< 2 days). Branch naming:
  `feat/<scope>-<slug>`, `fix/<scope>-<slug>`, `refactor/<slug>`, `docs/<slug>`, `chore/<slug>`.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/). Types: `feat`, `fix`,
  `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`.
- **PRs:** Squash-merge by default; minimum 1 approving review. PR template is mandatory.
- **Code style:** 4-space indent, LF endings, ruff-enforced. See `.editorconfig`.
- **Naming:** `snake_case` for modules/functions, `PascalCase` for classes, `UPPER_SNAKE_CASE`
  for constants.
- **Layers:** `ui → logic ← data`. Never the reverse.

## Setting up the project

1. Install Python 3.11+ and set it as default (`python --version`).
2. Create a virtualenv: `python -m venv .venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run `streamlit run main.py` to verify the app starts.
5. Read `docs/onboarding.md` for your first task.

Lint and tests run automatically on GitHub Actions at push/PR time; running them locally is
optional (see `docs/contributing/testing.md`).

## Commit format

```
<type>(<scope>): <subject>

<body>

<footer>
```

- `type`: see Quick reference.
- `scope`: `ui`, `data`, `scrape`, `projection`, `optimize`, `state`, `excel`, `docs`, `build`,
  `ci`.
- `subject`: imperative mood, lowercase, no trailing dot.
- `body`: explain what and why (not how — the diff shows how).
- `footer`: `BREAKING CHANGE: ...` for breaking changes; `Closes #123` for issues.

Example:

```
feat(optimize): maximize expected points with dynamic budget and slot constraints

Adds the PuLP squad optimizer in optimize.py with per-role slot constraints
and a per-player spending limit derived from opportunity cost.
```

## Pull-request checklist

Every PR must:

- [ ] Pass CI: `ruff check .`, `ruff format --check .`, `pytest` (all run on GitHub Actions).
- [ ] If touching public API: docstrings + type hints added.
- [ ] If touching logic (`projection.py`, `optimize.py`): unit tests added/updated.
- [ ] If touching scrapers: cache-first behaviour preserved; no live-network call in tests.
- [ ] CHANGELOG.md updated (Unreleased section).
- [ ] Docs updated if behaviour or conventions changed.

## Code conventions

- Types: `PascalCase`. Functions and variables: `snake_case`. Constants: `UPPER_SNAKE_CASE`.
- Public APIs: docstrings (Google style) mandatory, type hints everywhere.
- Entities: `@dataclass` (frozen when possible). Prefer pure functions in `logic`.
- No `print()` in production code — use the `logging` module.
- Every network call lives in a `fetch_*` module with a `User-Agent` header and rate limiting.
- No hard-coded endpoints, selectors or secrets scattered across the code: centralised
  `UPPER_SNAKE_CASE` constants in the owning `fetch_*` module.

## Documentation

- Markdown only, repo-relative links.
- Architecture decisions go in `docs/project/architecture/adr/`.
- Work items go in `docs/project/tasks/` (from `TASK_TEMPLATE.md`).
- Defects go in `docs/project/known_issues/` (one `KI-<N>.md` per issue, from
  `KNOWN_ISSUE_TEMPLATE.md`).
- Delivery gaps go in `docs/project/delivery_gap/` (one `DG-<N>.md` per gap, from
  `DELIVERY_GAP_TEMPLATE.md`).
- Agentic-tool rules live in `docs/agents/RULES.md`.

## Questions?

Open an issue with the label `question` or ask in the team channel.
