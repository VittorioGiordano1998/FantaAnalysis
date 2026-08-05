# Task: M6-T2 — Deploy su Streamlit Community Cloud

- **ID:** M6-T2
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** Medium
- **Area:** build

## Problem

PLANNING §7: deploy su Streamlit Community Cloud con link usabile da
telefono. Il repo ha già un remote GitHub
(`github.com/VittorioGiordano1998/FantaAnalysis`); manca il push dell'intera
implementazione M1-M6 e la verifica di prontezza per il Cloud.

## Proposed Solution

- Commit + push su `origin/main` dell'implementazione (messaggio secondo
  `docs/contributing/commits.md`).
- Checklist di prontezza Cloud:
  - `requirements.txt` completo (streamlit, pandas, openpyxl, pulp, ...);
  - nessun segreto versionato; `data/` e `output/` gitignored (cache
    rigenerabile con "Aggiorna dati");
  - stato asta round-trip via export/import bytes (ADR-0004) — il disco
    Cloud è effimero;
  - entrypoint `main.py` rilevato automaticamente da Cloud.
- Passi manuali utente (documentati nella Resolution): collegare il repo
  su share.streamlit.io, entrypoint `main.py`, Python 3.12, aprire il link.

## Notes

- Il push è esplicito in questo task (deploy richiesto dal piano);
  l'account Streamlit è dell'utente (non automatizzabile qui).

## Resolution

Repo pronto e pushato: commit in 3 parti logiche (scraper; logic
proiezione/ottimizzazione; ui/stato/excel + docs) su `origin/main`
(remote esistente `github.com/VittorioGiordano1998/FantaAnalysis`).
Checklist Cloud verificata: `requirements.txt` completo, nessun segreto
versionato, `data/` e `output/` gitignored (cache rigenerabile con
"Aggiorna dati"), stato asta round-trip bytes (ADR-0004), entrypoint
`main.py` auto-detectato, CI verde su push (ruff + pytest 71).

Passi manuali per l'utente (account Streamlit): su
share.streamlit.io → "Create app" → selezionare il repo, branch `main`,
entrypoint `main.py`, Python 3.12 → aprire il link dal telefono; dopo il
deploy eseguire "Aggiorna dati" per popolare la cache, poi esportare/
importare lo stato per la sessione.
