# Pull Requests

1. Branch from `main`: `feat/<scope>-<slug>` or `fix/<scope>-<slug>`.
2. Fill the PR template (`.github/pull_request_template.md`).
3. Squash-merge on approval. Minimum 1 approving review.

## Checklist

- [ ] CI passes: `ruff check .` (lint).
- [ ] CI passes: `ruff format --check .` (format).
- [ ] CI passes: `pytest` (unit tests).
- [ ] Docstrings + type hints on new public APIs.
- [ ] CHANGELOG.md updated (Unreleased section).
- [ ] Docs updated if behaviour or conventions changed.
- [ ] Logic changes (`projection.py`/`optimize.py`) have unit tests.
- [ ] Scraper changes keep cache-first behaviour; no live-network call in tests.
- [ ] Layer rules respected (RULES.md §Layers): no `ui` → `data` shortcuts, no I/O in `logic`.
