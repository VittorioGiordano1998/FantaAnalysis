## Summary

<what changed and why — 1–3 bullets>

## Linked issues / docs

- Closes #
- Updates `docs/...` (see PR Doc Sync checklist)

## Test plan

- [ ] CI passa: `ruff check .` (lint)
- [ ] CI passa: `ruff format --check .` (format)
- [ ] CI passa: `pytest` (test unitari)
- [ ] Manuale: `streamlit run main.py` senza errori
- [ ] Se tocca `logic` (projection/optimize): test unitari aggiornati
- [ ] Se tocca scraper: nessuna chiamata di rete nei test; cache-first preservata

## Risk

<low / medium / high — what could regress>

## Screenshots / Recordings

<if UI change>
