# Testing

## Unit tests (`tests/`)

- pytest, run with `pytest` (CI) or `python -m pytest` locally.
- `logic` (`projection.py`, `optimize.py`): pure unit tests, no I/O, no network.
- `data` (`fetch_*.py`): tested against recorded fixtures (sample HTML/CSV in `tests/fixtures/`)
  pointed to by the fetch functions — unit tests never hit the network and never depend on a
  live page structure.
- `state.py`: JSON round-trip tests using `tmp_path`; import/export bytes round-trip.
- `ui` (`main.py`, `pages/`): not unit-tested by default; manual verification via
  `streamlit run main.py`.

## Verification

The gate is **CI on GitHub Actions** (`.github/workflows/ci.yml`), which runs on every push/PR:

```
ruff check .              # lint
ruff format --check .     # format
pytest                    # unit tests
```

Locally (optional):

```
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Manual smoke test: `streamlit run main.py` — load the app, modify the auction state, verify the
squad recomputes.
