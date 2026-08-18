# ADR: Layer web per il mega listone (Next.js static, local-first)

- **Status:** Accepted
- **Date:** 2026-08-18
- **Decision-makers:** project owner

## Context

La schermata del mega listone vive in `main.py` (Streamlit) con tabella
full-screen, prese noi/altri, prezzo e budget. L'utente vuole la stessa
schermata e gli stessi campi/informazioni, ma resa con lo **stack e lo stile
grafico di Sphynx** (Next.js 16 + React 19 + TS + Tailwind 4, tema scuro,
badge/chip, glass card). Il resto dell'app resta su Streamlit. Il PuLP (Python)
non gira su Next.js: l'ottimizzazione è rimandata a un rewrite TS futuro, fuori
da questa fase. Riferimento: `PLANNING-WEB.md`, branch `web/`.

## Decision

- Nuova app in `web/` (branch `web/`): Next.js App Router con `output:
  'export'` (build statica), local-first **senza auth**, deploy su Vercel.
- L'app rispecchia in TypeScript la stessa entità display-only `ListoneRow`
  (`web/src/lib/types.ts`) e lo stesso stato `ListoneState` di `state.py` v2
  (budget, flags `"noi"|"altri"|""`, prices): **nessuna modifica di forma alle
  entità condivise, nessuna priorità manuale, nessuna colonna nuova**.
- La fonte del listone è `web/src/data/listone.json` (versionato), generato da
  `resources/listone.xlsx` con `tools/convert_listone.py` (replica di
  `fetch_listone.read_listone`). Lo Streamlit continua a leggere l'Excel.
- La persistenza dello stato è `localStorage` + export/import JSON tra device
  (niente backend, niente account).
- Il layer `web` è una **variante dell'interfaccia UI**: la `ui → logic ← data`
  del progetto resta valida per la parte Streamlit; la app web è autonoma e
  non dipende da `logic` Python.

## Consequences

- Più facile: stessa app su un solo stack moderno; offline dopo il build
  statico; deploy Vercel semplice; la logica di presa/budget resta identica
  (test portati in Vitest, `web/test/listone-state.test.ts`).
- Più difficile: due app in parallelo (Streamlit + web) finché le pagine
  laterali non saranno migrate; la fonte del listone è duplice (xlsx per
  Streamlit, json per web) — drift evitato riconvertendo con lo stesso script.
- Da rivalutare: la portabilità dell'ottimizzatore PuLP in TS (proiezioni +
  MILP) e, se un domani si migra tutto, il futuro di `main.py`/`pages/`.

## Alternatives considered

- **Restyling CSS su Streamlit:** respinto dall'utente — vuole lo stack di
  Sphynx, non un tema applicato a Streamlit.
- **Supabase/Capacitor come Sphynx:** posticipato — tool personale, local-first
  senza account; Capacitor non richiesto (PWA web responsive basta).
- **Backend Python separato per il PuLP:** tenuto come futura opzione solo se il
  rewrite TS del MILP risultasse insostenibile.
