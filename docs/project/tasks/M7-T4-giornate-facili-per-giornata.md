# Task: Giornate facili per giornata e ricerca inversa

- **ID:** M7-T4
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** logic | data | ui

## Problem

La % di utilità sintetica non basta: durante l'asta serve il calcolo
effettivo per giornata. Esempio: se il mio attaccante del Venezia ha
Napoli/Venezia (difficile) alla giornata X, voglio trovare un attaccante
rimasto che QUELLA giornata ha una partita facile.

## Proposed Solution

- `utility.py`: nuova `CalendarWeek(matchweek, opponent_id)`; `TeamCalendar`
  passa a `tuple[CalendarWeek, ...]` (numero di giornata incluso);
  `OpponentOutlook` guadagna `matchweek`. Nuove funzioni pure:
  `week_coverage(own_players, ...)` → per ogni giornata rimanente facili
  coperte/presenti (con flag "scoperta") e `easy_candidates(matchweek,
  players, ...)` → chi ha avversario facile in quella giornata.
- `fetch_fixtures.read_remaining_calendar`: popola i `CalendarWeek` col
  matchweek dal CSV.
- Home (`main.py`):
  - scheda Consigli: caption "Giornate facili: 12, 14, 17…";
  - nuova sezione "Copertura giornate facili": tabella copertura per tutte
    le giornate rimanenti (scoperte evidenziate) + ricerca inversa con
    selettore giornata (default: la più scoperta) e filtro ruolo → tabella
    rimasti con partita facile: Nome, Squadra, Ruolo, QI, Punti attesi.
  - calcoli cachati (`@st.cache_data`, chiave = giornata + ruolo + prese +
    refresh).
- Test: nuova forma `TeamCalendar`, matchweek in `opponent_outlook`,
  `week_coverage`, `easy_candidates`, `read_remaining_calendar` con numeri
  di giornata.

## Notes

- Si costruisce su M7-T3 (TeamCalendar), commit `f698928` ancora da pushare.
- Nessun ADR: nuovi tipi e funzioni pure in `utility.py`.

## Resolution

- `utility.py`: `CalendarWeek(matchweek, opponent_id)`; `TeamCalendar.weeks`
  al posto di `opponents`; `OpponentOutlook.matchweek`; nuove funzioni pure
  `week_coverage` (facili coperte/presenti per giornata, flag `uncovered`)
  e `easy_candidates(matchweek, players, ...)`; `_coverage` riusa
  `week_coverage`.
- `fetch_fixtures.read_remaining_calendar`: `CalendarWeek` con matchweek dal
  CSV; filtro `>= current_matchweek` (la giornata corrente è la prossima da
  giocare, coerente con `read_league_context`).
- `main.py`: caption "Giornate facili: 12, 14, 17…" nella scheda consigli;
  nuova sezione "Copertura giornate facili" in home: tabella copertura per
  tutte le giornate rimanenti (scoperte evidenziate, attiva con le prime
  prese) + ricerca inversa con selettore giornata (default: più scoperta,
  altrimenti la prima) e filtro ruolo → rimasti con partita facile
  (Nome, Squadra, Ruolo, QI, Punti attesi) ordinati per punti, cachata
  (`_easy_at_week`, chiave = giornata + ruolo + prese + refresh).
- 8 test nuovi/aggiornati: nuova forma `TeamCalendar`, matchweek in
  `opponent_outlook`, `week_coverage` (conteggi, flag uncovered, vuoto),
  `easy_candidates` (filtro per giornata e regola per ruolo),
  `read_remaining_calendar` (cache assente → `{}`, settimane ≥ corrente).
- Verifica: `pytest` → 99/99; `ruff check .` pulito; smoke test AppTest con
  dati reali: 38 giornate disponibili, ricerca inversa funzionante
  (giornata 2, Attaccanti → 48 candidati ordinati per punti, es. Martinez
  L. 140.6).

## Note

- I due commit M7-T3 (`f698928`) e M7-T4 sono da pushare insieme.
