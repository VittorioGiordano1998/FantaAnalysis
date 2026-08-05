# Task: M2-T1 — Scraper statistiche giocatori

- **ID:** M2-T1
- **Status:** Done
- **Date opened:** 2026-08-05
- **Date done:** 2026-08-05
- **Severity:** High
- **Area:** data

## Problem

Le proiezioni punti (M3) hanno bisogno delle statistiche stagionali per
giocatore (partite, gol, assist, cartellini, rigori, medie voto). Fonti
plausibili (pagina giocatore singolo) richiederebbero ~494 richieste; serve
una pagina lista che esponga i dati di tutti i giocatori in un colpo solo.

## Proposed Solution

Verificato: `https://www.fantacalcio.it/statistiche-serie-a` rende server-side
una tabella `#stats` con tutti i 494 giocatori del listone (paginazione
client-side): PV, MV, FM, Gol, GS, Rig (segnati/tirati), RP, Ass, Amm, Esp,
squadra, ruolo Mantra, URL pagina giocatore. Un solo GET.

- Nuovo modulo `fetch_stats.py` (layer data), stesso pattern di
  `fetch_quotazioni`: funzione pura `parse_statistiche_html(html)`,
  cache-first settimanale `data/statistiche.csv` (7 giorni),
  `get_statistiche(force_refresh=False)`.
- Campi: season, name, role, role_label, team_id, team_code,
  played_matches, grade_avg (MV, decimale con virgola), fanta_avg (FM),
  goals, goals_against, penalties_scored, penalties_total, penalties_saved,
  assists, yellow_cards, red_cards, player_url.
- Fixture registrate: stagione corrente (2026/27, valori a zero) e 2025/26
  (valori reali) + test senza rete.
- Nota: i minuti giocati NON sono esposti da Fantacalcio.it (verificato su
  pagina lista e pagina giocatore) → file Known Issue separato.

## Notes

- Selettori e URL come costanti `UPPER_SNAKE_CASE` nel modulo proprietario.
- Nessun test tocca la rete.

## Resolution

Creato `fetch_stats.py` (layer data): GET unico di `/statistiche-serie-a`
(tabella `#stats`, tutti i 494 giocatori, paginazione client-side), parsing
puro `parse_statistiche_html` con selettori per `data-col-key` (pg, mv, mfv,
gol, gs, rig, rp, ass, amm, esp), ruolo Mantra, team id/codice, URL
giocatore; decimali con virgola italiana via `fetch_common.to_decimal`.
Cache-first settimanale `data/statistiche.csv` con `get_statistiche(
force_refresh=False)`. Refactoring: helper condivisi spostati in
`fetch_common.py` (fetch_html con UA/rate-limit, to_int/to_decimal,
is_cache_fresh, read_cache_frame, write_csv) e riusati da
`fetch_quotazioni.py` (API invariata, test M1 ancora verdi).

Fixture registrate (slice reali): `statistiche_2026_27.html` (25 righe,
valori a zero) e `statistiche_2025_26.html` (25 righe, valori reali: De Luca
MV 7,0 / FM 10,0 / 1 gol / rigori 1/1). `tests/test_fetch_stats.py`: 7 test
senza rete (conteggio, valori noti, ruoli, decimali, round-trip CSV su
tmp_path, riuso cache). Verificato end-to-end con fetch reale: 494 giocatori,
12 ruoli, CSV scritto. CI verde (ruff + pytest 20/20 complessivi).

Nota: i minuti giocati non sono esposti da Fantacalcio.it → KI-1.
