# FantaOptimizer Web — Planning del mega listone su stack Sphynx (Next.js)

> Documento di planning per la migrazione del **solo mega listone** (oggi `main.py`
> su Streamlit) verso una app **Next.js 16 + React 19 + TypeScript + Tailwind**,
> in **stile grafico identico a Sphynx**, local-first senza auth, deploy statico
> su **Vercel**. Aggiornato con le decisioni del team.

---

## Obiettivo

Spostare la schermata del **mega listone** su Next.js mantenendo **tutti i campi,
le colonne e le informazioni attuali** (ruoli Mantra, squadra, titolarità, FMV,
rigorista/punizioni/angoli con priorità, preso noi/altri), ma renderizzata con il
**look grafico del progetto Sphynx** (tema scuro, badge/chip, tipografia, glass
card, scrollbar). Le altre pagine (Analisi, RosaOttimale, Guide, GuidaAsta)
**restano su Streamlit** e continuano a funzionare invariate.

Non si introducono nuove funzioni: si riscrive la visualizzazione del listone su
un altro stack, con la stessa logica di presa, prezzo e budget.

---

## Decisioni chiave

| Argomento | Decisione |
|-----------|-----------|
| **Scope** | Solo il mega listone; il resto resta su Streamlit, che coesiste. |
| **Branch** | Tutto il lavoro web vive nel branch **`web/`**; la logica Streamlit resta intatta su `main`/`deploy`. |
| **Rendering** | **Tabella dati in stile Sphynx** (niente card/kanban). |
| **Fonte listone** | **`listone.json` versionato nel repo**, generato da `Listone.xlsx` con uno script dedicato. |
| **Backend** | **Local-first senza auth**: stato in `localStorage` + export/import JSON (telefono ↔ desktop). |
| **Ottimizzatore** | PuLP (Python) non gira su Next.js: **rewrite TypeScript futuro**, fuori da questa fase. |
| **Mobile** | **Web responsive + PWA** (installabile); niente Capacitor. |
| **Deploy** | **Vercel** collegato al ramo `web/` (static export `out/`). |

---

## Stack

Stesso set base di Sphynx (da `Sphynx/package.json`), semplificato: senza Supabase
e senza Capacitor.

- **Next.js 16** (App Router) con `output: 'export'` (build statica).
- **React 19** + **TypeScript 5**.
- **Tailwind CSS 4**.
- **lucide-react** (icone), **clsx** + **tailwind-merge** + **class-variance-authority**.
- **zustand** per lo stato client (prese/budget) — leggero e mobile-friendly.
- PWA: `public/manifest.webmanifest` + icone + service worker.

---

## Architettura

```
Utente (telefono o desktop, browser / PWA)
        │
        ▼
   Next.js static build (out/)
        │
        ├── listone.json (repo, versionato)
        │
        └── localStorage (stato presa/budget per device)
              └── export/import JSON (spostare stato tra device)
```

- **Online-first** in lettura dal bundle statico; poi completamente **offline** (PWA).
- Nessun backend, nessun account, nessuna rete esterna a runtime.
- Nota esplicita nel README: lo stato è **per device**; per passarlo da un device
  all'altro si usa export/import del JSON.

---

## Struttura dei file (nel ramo `web/`)

```
FantaAnalysis/
├── main.py / pages/ / fetch_*      # Streamlit invariato (coesiste)
├── resources/listone.xlsx          # fonte dell'utente (invariata)
├── tools/convert_listone.py        # NUOVO: xlsx → web/src/data/listone.json
└── web/                            # NUOVA app Next.js (stile Sphynx)
    ├── package.json
    ├── next.config.ts              # output:'export', trailingSlash
    ├── tsconfig.json
    ├── .gitignore                  # node_modules, .next, out
    ├── public/
    │   ├── manifest.webmanifest    # PWA
    │   └── icons/                  # icone PWA
    └── src/
        ├── app/
        │   ├── globals.css         # palette .dark copiata da Sphynx (oklch identiche)
        │   ├── layout.tsx          # font heading (Cinzel), manifest
        │   └── page.tsx            # schermata listone
        ├── components/listone/
        │   ├── listone-table.tsx   # tabella dati in stile Sphynx
        │   ├── toolbar.tsx         # ricerca, filtri, pulsanti presa, budget
        │   ├── badges.tsx          # chip priorità + dot stato
        │   └── state-export.tsx    # export/import JSON stato
        ├── lib/
        │   ├── types.ts            # ListoneRow, ListoneState, Role (mirror entities.py)
        │   └── listone-state.ts    # localStorage + toggle + budget residuo
        └── data/
            └── listone.json        # dati versionati (generato)
```

---

## Modello dati (mirror di `entities.py` / `state.py`)

### `Role` (12 codici, da `entities.py`)
`por, dc, b, dd, ds, e, m, c, w, t, a, pc` — stesso enum.

### `ListoneRow` (readonly, display-only)
| Campo TS | Equivalente Python | Tipo |
|---|---|---|
| `name` | `ListoneRow.name` | `string` |
| `teamName` | `team_name` | `string` |
| `roles` | `roles` | `Role[]` |
| `titolarita` | `titolarita` | `number \| null` |
| `fmv` | `fmv` | `number \| null` |
| `rigorista` | `rigorista` | `number \| null` (priorità 1/2/3) |
| `punizioni` | `punizioni` | `number \| null` |
| `angoli` | `angoli` | `number \| null` |
| `presoNoi` | `preso_noi` | `boolean` |
| `presoAltri` | `preso_altri` | `boolean` |

### `ListoneState` (== formato v2 di `state.py`)
| Campo | Tipo |
|---|---|
| `budget` | `number` |
| `flags` | `Record<string, "noi" \| "altri" \| "">` |
| `prices` | `Record<string, number>` |

**Stessi 3 stati, nessuna colonna nuova, nessuna priorità manuale.**

---

## Convertitore Excel → JSON

`tools/convert_listone.py` (Python; riusa `pandas` + `openpyxl` già nel progetto).
Replica esattamente `fetch_listone.read_listone`:

- ruoli per spunta (`_ROLE_COLUMNS`, ordine del file);
- titolarità % e FMV come `float | null`;
- priorità rigorista/punizioni/angoli come `1/2/3`, vecchia spunta `✔` → `3`;
- righe vuote in coda escluse (campo "Giocatore" vuoto);
- output deterministico su `web/src/data/listone.json`.

Opzionale: hash SHA-256 del JSON per il check di integrità nella UI (deploy
stantio).

---

## UI in stile Sphynx

### Palette `.dark` copiata da `Sphynx/src/app/globals.css`
Variabili identiche (elementi CSS `--background`/`--card`/`--muted`/`--border`/
`--primary`/`--sphynx-card-bg`), raggio `0.75rem`, utility `glass`/`glass-strong`,
scrollbar sottile 6px.

### Tipografia
Headings uppercase con `letter-spacing 0.12em`, font heading (Cinzel via
`next/font`) come `Sphynx/src/app/layout.tsx`.

### Tabella dati (niente card)
- Righe colorate per stato: presa da noi → tinta **verde/emerald**; presa da altri
  → tinta **rossa/rose** — in dark palette Sphynx.
- Titolarità a soglie (95/75/50/25) e FMV ≥ 6 con gli **stessi significati** del
  file Excel, declinati in tinte scure leggibili.
- Rigorista / punizioni / angoli mostrati come **chip di priorità** (colori
  `PRIORITY_CLASS` da `tasks-view.tsx:144`: verde/ambra/rossa in dark variant).
- Stato mostrato anche come **dot/badge** (`TASK_STATUS_COLOR` da
  `team-profile-card.tsx:40`).

### Comportamento invariato (port da `main.py`)
- Selezione righe → pulsanti **"Preso da noi" / "Preso da altri"** (toggle),
  **prezzo pagato** e **budget residuo**.
- Filtri: ricerca per nome, squadra, gruppo ruolo (multiruolo incluso);
  contatori giocatori rimasti + residuo budget.
- Toolbar in glass-card Sphynx.

### Mobile / PWA
Tabella con scroll orizzontale, toolbar compatta, installabile da telefono;
stato per device con export/import JSON.

---

## Deploy (Vercel)

- Progetto **Vercel** collegato al repo GitHub, branch **`web/`**, framework
  Next.js, build command `npm run build` (output statico `out/`).
- A ogni push su `web/` Vercel ridisegna automaticamente il listone; HTTPS
  gratuito e supporto PWA nativo.
- Flusso di aggiornamento (documentato): sostituisci `Listone.xlsx` →
  `python tools/convert_listone.py` → verifica diff su `listone.json` → commit
  su `web/` → auto-deploy.
- Il ramo `deploy` (Streamlit Cloud) resta **indipendente e invariato**.

---

## QA / CI

- Job Actions dedicato (trigger sul ramo `web/`): `npm ci` → `lint` → `build`.
- I job esistenti (ruff lint+format, pytest) di Streamlit restano intatti.
- Verifica manuale: build statico + serve di `out/`; 352 giocatori reali; toggle
  presa/prezzo/budget; export/import stato; PWA installabile su telefono.

---

## Docs (task-first del repo)

- Task `docs/project/tasks/M10-T1-mega-listone-web.md` (dal `TASK_TEMPLATE.md`),
  chiusa con `Status: Done` + `Resolution` di verifica.
- **ADR-0006** `docs/project/architecture/adr/ADR-0006-web-listone-nextjs.md`:
  introduce il layer `web` (variante UI static/local-first della stessa entità
  display-only `ListoneRow`). Nessun cambio di forma/semantica → nessuna modifica
  alla logica Streamlit, nessun bump di `LOGIC_VERSION`/`version.txt`.
- `PLANNING-WEB.md` (questo file) alla root + riga in `CHANGELOG.md`.
- `README.md`: sezione "Web (mega listone)" con istruzioni di build e deploy.

---

## Ordinamento lavoro

1. Branch `web/` + scaffold Next/Tailwind/PWA + `globals.css` Sphynx.
2. `tools/convert_listone.py` → `web/src/data/listone.json`.
3. Tipi + stato local-first + export/import.
4. Tabella in stile Sphynx (filtri / prese / budget / badge).
5. Responsive + PWA.
6. CI web + test + ADR / task / CHANGELOG.
7. Collega Vercel al ramo `web/` e verifica il deploy.
