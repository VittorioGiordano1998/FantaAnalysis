# FantaOptimizer

Web app (Streamlit) per il fantacalcio **Serie A 2026/27** — Asta 500M, regolamento **Mantra**,
listone ufficiale Fantacalcio.it. Usabile dal telefono durante l'asta: tiene traccia dello stato
dell'asta, ricalcola in tempo reale la rosa ottimale tra i giocatori rimasti e suggerisce quanto
offrire al massimo per ogni giocatore.

Il piano completo è in [`PLANNING.md`](PLANNING.md).

## Funzionalità

- Stato asta live: giocatori presi, budget speso/residuo, slot per ruolo (P, DC, DD, DS, E, M, CC,
  W, T, PC).
- Rosa ottimale tra i rimasti: ottimizzazione PuLP con vincoli dinamici (budget + slot mancanti,
  rosa 2P-8D-8C-7A).
- Limite di spesa consigliato per giocatore (punti attesi − costo opportunità).
- Analisi: proiezioni punti per ruolo, calendario facile/difficile, top qualità/prezzo.
- Persistenza stato (JSON) con esporta/importa; export report Excel.
- Aggiornamento dati con cache settimanale (pulsante "Aggiorna dati").

## Quick start

1. **Prerequisiti:** Python 3.11+ (vedi `docs/onboarding.md`).
2. **Installa:** `pip install -r requirements.txt`.
3. **Avvia:** `streamlit run main.py`.

Per pubblicare l'app su Streamlit Community Cloud (o testarla in locale senza
deploy) segui [`docs/deploy.md`](docs/deploy.md).

La verifica di qualità (lint + test) gira automaticamente su GitHub Actions al push:
vedi `docs/contributing/testing.md` per i comandi locali opzionali.

## Architettura

- **UI:** Streamlit (`main.py` + `pages/`).
- **Logic:** proiezioni punti (`projection.py`) e ottimizzazione (`optimize.py`) — calcolo puro.
- **Data:** scraping (`fetch_quotazioni.py`, `fetch_stats.py`, `fetch_fixtures.py`) e stato asta
  (`state.py`) — ogni I/O vive qui.

Dipendenza tra layer:

```
ui → logic ← data
```

mai la direzione inversa.

## Web (mega listone, Next.js in stile Sphynx)

Sul branch `web/` vive una app **Next.js** (stack di Sphynx: React 19 + TypeScript +
Tailwind 4) che riproduce il **mega listone** (stessi campi, prese noi/altri, prezzo,
budget) con il tema scuro Sphynx. Piano in [`PLANNING-WEB.md`](PLANNING-WEB.md),
ADR-0006.

```bash
cd web
npm ci
npm run dev        # sviluppo: http://localhost:3000
npm run build      # export statico in web/out
npm run preview    # serve l'export statico (richiede npx serve)
```

- **Fonte dati:** `web/src/data/listone.json` (versionato). Dopo aver aggiornato
  `resources/listone.xlsx` rigenera il JSON e committalo:

  ```bash
  python tools/convert_listone.py
  ```

- **Stato (local-first):** salvato nel browser (`localStorage`), **per device**; usa i
  pulsanti *Importa/Esporta* in alto per spostarlo tra telefono e desktop.
- **Deploy:** Vercel, branch `web/` (static export). Streamlit Cloud resta per le altre
  pagine sul ramo `deploy`.
- **Verifica:** `npm run lint`, `npm run test`, `npm run typecheck`; CI sul branch `web/`.

## Contribuire

Vedi [`CONTRIBUTING.md`](CONTRIBUTING.md) per branch, commit, code style e convenzioni PR.

## Documentazione

- [`docs/`](docs/) — architettura, ADR, guide contributing, roadmap.
- [`docs/onboarding.md`](docs/onboarding.md) — guida per il primo contributo.
- [`docs/agents/RULES.md`](docs/agents/RULES.md) — regole condivise per i tool agentici
  (Claude Code & opencode).

## Fonti dati e note legali

I dati (quotazioni, statistiche, calendario) vengono da Fantacalcio.it e Understat, usati solo
per uso personale e soggetti ai loro termini; il progetto non è affiliato a Fantacalcio.it.
