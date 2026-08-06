# Task: Utilità sul calendario completo e gestione pre-stagione

- **ID:** M7-T3
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** logic | data | ui

## Problem

Nei consigli di acquisto (M7-T2) il calendario valuta solo le prossime 5
giornate e, a stagione non iniziata (nessun match giocato → medie di lega
`None`), `calendar_ease` è sempre 0% e `coverage` sempre 50%: il consiglio
è inutile proprio nel periodo dell'asta (agosto). L'utente chiede la
valutazione su tutto il calendario rimanente.

## Proposed Solution

- `utility.py`: nuova entità `TeamCalendar(team_id, opponents)` con tutti gli
  avversari delle giornate rimanenti (ordinati per matchweek). `utility_score`
  e `opponent_outlook` valutano tutto il calendario rimanente, non più 5
  giornate.
- Gestione dati assenti: `OpponentOutlook.easy` diventa `bool | None`
  (None = sconosciuto); nella media i valori sconosciuti pesano 0.5 (neutro)
  invece di 0. Quando le medie di lega mancano (pre-stagione) si usa come
  fallback la forza squadra stimata dal listone: `team_strengths_from_players`
  (media FVM per squadra) con benchmark = media dei proxy.
- `fetch_fixtures.read_remaining_calendar(cache_dir)` → `dict[team_id,
  TeamCalendar]` (cache assente → `{}`); helper `_current_matchweek(frame)`
  condiviso con `read_league_context`. `ui_common.get_calendars` cachato.
- `main.py`: `_advice_for` passa calendar + proxy e ritorna anche
  `has_results` (medie reali disponibili) e il numero di giornate rimanenti;
  caption esplicita ("stagione non iniziata: forza stimata dal listone").
- Test: calendario completo (avversario facile oltre la 5ª giornata
  conteggiato), ignoto → 0.5, proxy FVM, stesso calendario per tutti i team.

## Notes

- La proiezione punti (projection.py) mantiene il moltiplicatore a 5
  giornate (ADR-0002): l'estensione riguarda solo l'utilità.
- Nessun ADR: nuove funzioni pure e nuovi tipi in `utility.py`, nessuna
  modifica a entità esistenti.

## Resolution

- `utility.py`: nuova entità `TeamCalendar(team_id, opponents)` (tutte le
  giornate rimanenti, ordinate per matchweek); `utility_score` e
  `opponent_outlook` accettano `calendar` e `team_strengths`; `easy` è ora
  `bool | None` (ignoto → 0.5 neutro in `_ease_mean`); nuovo
  `team_strengths_from_players` (media FVM per squadra) usato come fallback
  quando le medie di lega mancano (pre-stagione).
- `fetch_fixtures.py`: `read_remaining_calendar(cache_dir)` (cache assente →
  `{}`) e helper `_current_matchweek(frame)` condiviso con
  `read_league_context`.
- `ui_common.py`: `get_calendars` cachato per flag refresh.
- `main.py`: `_advice_for` passa calendar + proxy e ritorna anche
  `has_results`; caption esplicite: lista "Avversari facili", "Stagione non
  iniziata: forza squadra stimata dal listone..." o "Nessun avversario
  facile tra le giornate rimanenti".
- 5 nuovi test: calendario completo oltre la 5ª giornata, ignoto → 0.5,
  proxy pre-stagione, `team_strengths_from_players`, copertura sul
  calendario completo.
- Verifica: `pytest` → 92/92; `ruff check .` pulito; smoke test con dati
  reali pre-stagione: Calendario 62% (prima 0%), Utilità 37% (prima 17%),
  lista avversari facili sul resto della stagione.
