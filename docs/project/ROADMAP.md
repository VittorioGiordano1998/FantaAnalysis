# Roadmap

Milestones for FantaOptimizer, derived from `PLANNING.md` §10. Work items for each milestone live
in `docs/project/tasks/`.

## M0 — Skeleton

- [x] Governance scaffold: `AGENTS.md`, `docs/agents/RULES.md`, task-first workflow
      (`TASK_TEMPLATE.md`, `KNOWN_ISSUE_TEMPLATE.md`, `DELIVERY_GAP_TEMPLATE.md`), slash
      commands (`/new-page`, `/new-task`, `/new-issue`, `/new-dg`).
- [x] CI: ruff lint + format check + pytest (GitHub Actions). Verification runs on the web —
      no local toolchain required.
- [x] ADR-0001: tech stack and layer rules (`ui → logic ← data`).

## M1 — Scraper quotazioni

- [ ] `fetch_quotazioni.py`: scrape quotazioni Fantacalcio.it (QI, QA, FVM, squadra, ruolo
      Mantra) → CSV cache settimanale in `data/`.
- [ ] Fixture HTML registrata + test senza rete.
- [ ] Pulsante "Aggiorna dati" (invalida la cache).

Tasks (`docs/project/tasks/`): M1-T1 scraper quotazioni + cache CSV, M1-T2 fixture e test,
M1-T3 invalidation cache.

## M2 — Scraper statistiche e calendario

- [x] `fetch_stats.py`: gol, assist, minuti, cartellini, rigori per giocatore.
- [x] `fetch_fixtures.py`: calendario Serie A (forza avversarie per proiezioni).
- [x] Cache settimanale + fixture e test per entrambi.

Tasks: M2-T1 scraper statistiche, M2-T2 scraper calendario.

## M3 — Proiezioni punti

- [x] `projection.py`: punti fanta attesi per ruolo Mantra (stats in corso + FVM + minuti,
      aggiustamento calendario su 5 giornate).
- [x] Tipi condivisi (`Player`, `Quote`) come `@dataclass` in `logic`.

Tasks: M3-T1 modello punti per ruolo, M3-T2 aggiustamento calendario, M3-T3 test unitari.

## M4 — Ottimizzatore

- [x] `optimize.py`: PuLP, massimizza punti attesi della rosa 2P-8D-8C-7A con budget 500M e
      slot per ruolo, solo giocatori rimasti.
- [x] Limite di spesa per giocatore (punti attesi − costo opportunità).
- [x] `@st.cache_data` sui risultati chiave per input.

Tasks: M4-T1 modello PuLP, M4-T2 limite di spesa, M4-T3 caching e performance.

## M5 — UI Streamlit e stato asta

- [x] `main.py` + `pages/`: stato asta live, rosa ottimale, limite spesa, analisi.
- [x] `state.py`: JSON stato asta + export/import (Streamlit Cloud, niente disco persistente).

Tasks: M5-T1 stato asta interattivo, M5-T2 pagina rosa ottimale, M5-T3 pagina analisi,
M5-T4 export/import stato.

## M6 — Export Excel e deploy

- [x] Report Excel (`output/`): rosa ottimale, giocatori rimasti, classifica per ruolo,
      calendario, qualità/prezzo.
- [x] Deploy: GitHub repo + Streamlit Community Cloud, link usabile da telefono.

Tasks: M6-T1 export Excel, M6-T2 deploy Streamlit Cloud.

## M7 — Test end-to-end

- [ ] Test e2e con dati reali: asta simulata dalla presa del primo giocatore alla rosa finale.

## Verification

Per milestone, i PR devono passare la checklist in `docs/contributing/pull-requests.md`
(CI verde: ruff lint + format, pytest). La conformità ai layer (`ui → logic ← data`) è un item
di review manuale finché non esiste un check automatico — se diventa dolore reale, si apre una
delivery gap.
