# Task: M6-T1 — Export report Excel

- **ID:** M6-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** Medium
- **Area:** data

## Problem

PLANNING §2 (#7): export Excel con rosa ottimale, giocatori rimasti,
classifica per ruolo, calendario, qualità/prezzo. `output/` (gitignored)
esiste come destinazione ma nessun modulo genera report.

## Proposed Solution

- `export_excel.py` (layer data, openpyxl): `build_report(squad, players,
  league, taken_urls) -> bytes` con 5 fogli (Rosa ottimale, Rimasti,
  Classifica per ruolo, Calendario, Qualità/prezzo), intestazioni in
  grassetto, freeze riga 1, larghezza colonne autofit; `save_report(bytes,
  path)` → `output/report_YYYYMMDD_HHMM.xlsx`.
- Etichette ruolo/gruppo italiane spostate in `entities.py`
  (`ROLE_LABELS`, `GROUP_LABELS`) e riusate da `ui_common`/`Analisi`
  (un'unica fonte).
- UI: in `main.py` (sidebar) "Report Excel" con `st.download_button` sui
  bytes cachati per snapshot; rosa non realizzabile → avviso.
- `tests/test_export_excel.py`: fogli e contenuti verificati con openpyxl
  su bytes/tmp_path.

## Notes

- La UI non tocca file: genera bytes via `build_report` e li salva solo
  localmente con `save_report` quando serve.

## Resolution

Creato `export_excel.py` (layer data, openpyxl): `build_report(squad,
players, league, taken_urls) -> bytes` con 5 fogli (Rosa ottimale con
TOTALE, Rimasti, Classifica per ruolo, Calendario con media di lega,
Qualità prezzo top 30), intestazione in grassetto, freeze A2, autofit;
`save_report` → `output/report_<timestamp>.xlsx` (gitignored). Etichette
ruolo/gruppo centralizzate in `entities.py` (`ROLE_LABELS`,
`GROUP_LABELS`), riusate da ui/export (un'unica fonte). UI: in `main.py`
sidebar "Scarica report Excel" con `st.download_button` sui bytes cachati
per snapshot (rosa non realizzabile → info). `tests/test_export_excel.py`:
7 test su bytes/tmp_path.

Verifica: suite 71 test verdi; report reale con 5 fogli, rosa 25+TOTALE
(1493.8 punti / 500 crediti), 494 rimasti.
