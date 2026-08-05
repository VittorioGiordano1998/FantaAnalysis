# Task: M1-T2 — Fixture HTML e test senza rete

- **ID:** M1-T2
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** data

## Problem

La regola di test (RULES §External services, `docs/contributing/testing.md`)
vieta agli unit test di toccare la rete: ogni scraper deve essere testato
contro fixture registrate da pagine reali. Senza fixture non c'è verifica
automatizzata del parsing di M1-T1.

## Proposed Solution

- Registrare `tests/fixtures/quotazioni_2026_27.html`: slice reale della
  pagina `fantacalcio.it/quotazioni-fantacalcio` (stagione 2026/27),
  ritagliata al body (tutta la struttura di filtro + tabella `#prices`).
- `tests/test_fetch_quotazioni.py`:
  - parsing della fixture → numero righe atteso, campi noti verificati
    (es. Martinez L. → pc / Punta centrale / INT / QI 35 / FVM 370);
  - mappa squadre da `select#team`;
  - stagione letta correttamente;
  - `rows_to_csv` → round-trip `read_quotazioni` su `tmp_path`.

## Notes

- La fixture è testo reale registrato (non generato a mano).
- Nessun test esegue richieste HTTP.

## Resolution

Registrata la fixture `tests/fixtures/quotazioni_2026_27.html` (slice reale
del body della pagina, stagione 2026/27, 494 righe). `tests/test_fetch_quotazioni.py`:
8 test senza rete — conteggio giocatori, campi noti (Martinez L. → pc/Punta
centrale/INT/Inter/QI 35/FVM 370/URL), stagione 2026/27, copertura dei 12
codici ruolo Mantra, 20 squadre, round-trip CSV su `tmp_path`, riuso cache
senza rete. Aggiunto `pythonpath = ["."]` in pyproject per l'import da root.

pytest: 8/8 verdi; nessun test esegue richieste HTTP.
