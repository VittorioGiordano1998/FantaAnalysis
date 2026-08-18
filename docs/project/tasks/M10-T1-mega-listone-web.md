# Task: M10-T1 — Mega listone web (Next.js, stile Sphynx)

- **ID:** M10-T1
- **Status:** Done
- **Date opened:** 2026-08-18
- **Date done:** 2026-08-18
- **Severity:** High
- **Area:** ui | build

## Problem

Il mega listone oggi vive in `main.py` (Streamlit) a schermata unica con
tabella e prese noi/altri. L'utente vuole la stessa schermata e gli stessi
campi/informazioni, ma **sullo stack di Sphynx** (Next.js 16 + React 19 +
TypeScript + Tailwind 4) e con il **look grafico Sphynx** (tema scuro,
badge/chip, glass card, tipografia). Il resto dell'app resta su Streamlit;
il lavoro vive sul branch `web/`. Riferimento: `PLANNING-WEB.md`.

## Proposed Solution

- Branch `web/` con nuova app in `web/` (Next.js App Router, `output:
  'export'`, Tailwind 4, zustand, lucide-react, PWA).
- `globals.css` con la palette `.dark` copiata da Sphynx; tabella dati in
  stile Sphynx con badge/dot, mantenendo tutte le colonne e il flusso attuali
  (selezione → "Preso da noi/altri", prezzo, budget residuo, filtri).
- Fonte dati: `listone.json` versionato in `web/src/data/`, generato da
  `resources/listone.xlsx` via `tools/convert_listone.py` (replica di
  `fetch_listone.read_listone`).
- Stato local-first senza auth: `localStorage` + export/import JSON.
- Deploy: Vercel sul branch `web/` (azione manuale utente).
- CI web: job Actions dedicato (`npm ci` → lint → build).

## Notes

- Ottimizzatore PuLP → rewrite TS: **fuori scope** (fase futura); qui non
  serve al listone.
- Le entità `ListoneRow`/`ListoneState` vengono rispecchiate in TS senza
  cambiarne forma/semantica → nessuna modifica alla logica Streamlit, nessun
  bump di `LOGIC_VERSION`/`version.txt`. Nuovo ADR-0006 per il layer `web`.
- Streamlit continua a leggere `resources/listone.xlsx` (invariato).

## Resolution

Implementato sul branch `web/` (ADR-0006):

- `web/`: app Next.js 16 + React 19 + TypeScript + Tailwind 4, `output:
  'export'`, tema scuro Sphynx (`globals.css` con palette `.dark` da
  `Sphynx/src/app/globals.css`), PWA (manifest + icone 192/512). Pagina unica
  `src/app/page.tsx` con tabella dati in stile Sphynx: stessi campi del file
  Excel (giocatore, ruoli multiruolo, squadra, titolarità a soglie, FMV,
  rigorista/punizioni/angoli con chip priorità, prezzo pagato), badge/dot di
  stato (Libero/Noi/Altri), selezione righe → "Preso da noi"/"Preso da altri"
  (toggle, come lo Streamlit), budget residuo, filtri nome/squadra/gruppo ruolo.
- Fonte: `web/src/data/listone.json` (351 giocatori, versionato) generato da
  `resources/listone.xlsx` con `tools/convert_listone.py` (stesso schema di
  `fetch_listone.read_listone`; `presoNoi/Altri = _optional_bool`).
- Stato local-first: `lib/listone-state.ts` (zustand + localStorage, formato v2)
  con logic pure identiche a `state.py`/`_toggle_flags`; export/import JSON tra
  device tramite `StateExport`.
- Test: `web/test/listone-state.test.ts` (Vitest, 11 test passati) e
  `tests/test_convert_listone.py` (pytest, 2 test passati); `ruff check .` e
  `ruff format --check .` puliti (intero repo); `npm run lint`, `typecheck`,
  `build` puliti; render statico `out/` verificato (h1, righe giocatore,
  manifest).
- CI: job `web` in `.github/workflows/ci.yml` (npm ci → lint → test → build →
  typecheck), attivo quando `web/` è presente (branch `web/`/PR).
- Docs: `PLANNING-WEB.md`, ADR-0006, CHANGELOG (sezione Added), README (sezione
  "Web (mega listone…)"), `vercel.json` (rootDirectory `web`), task chiusa.
- Limitazioni: lo stato è per device (niente sync — export/import manuale); il
  PuLP non è ancora portato in TS (fase futura); il deploy su Vercel è
  un'azione manuale dell'utente (progetto → branch `web/`, root directory
  `web`).
