# ADR: Shared entities and projection model

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision-makers:** project owner

## Context

M3 introduces the shared truth of the app: the entity shapes that both the
live path and the cached path converge on, and the semantics of the point
projection used by the optimizer (PLANNING §5, M3 of the roadmap). Two
forces make this decision non-trivial:

1. RULES require `logic` to be pure and the single source of truth; entity
   shape changes must go through an ADR.
2. The data available is constrained: Fantacalcio.it does not expose minutes
   played (KI-1) and, at auction time, the season has not started (all
   season stats are zero). The model must degrade gracefully: work with
   zero data at week 1 and become sharper as the season progresses.

## Decision

### Entities (`entities.py`, layer logic)

- `Role` (StrEnum) with the 12 Fantacalcio.it Mantra codes:
  `por, dc, b, dd, ds, e, m, c, w, t, a, pc`.
- `RoleGroup` (Enum): `P, D, C, A`; mapping `ROLE_GROUP`:
  - P: `por`;
  - D: `dc, b, dd, ds`;
  - C: `e, m, c, w, t`;
  - A: `a, pc`.
- `Quote`: `qi: int | None`, `qa: int | None`, `fvm: int | None`.
- `SeasonStats`: played_matches, grade_avg (MV), fanta_avg (FM), goals,
  goals_against, penalties_scored, penalties_total, penalties_saved,
  assists, yellow_cards, red_cards (all `int | None` / `float | None`).
- `Player`: `name`, `role: Role`, `team_id`, `team_code`, `team_name`,
  `quote: Quote`, `url` (pagina giocatore, chiave di join con le stats),
  `stats: SeasonStats | None` (default `None`).
- `attach_stats(players, stats_by_url) -> list[Player]`: merge puro delle
  stats per `player.url` (assemblea, non I/O).

### Projection (`projection.py`, layer logic)

Constants: `SEASON_MATCHWEEKS = 38`, `NEXT_WEEKS = 5`,
`MIN_MATCHES_FOR_STATS = 3`, `FVM_PPM_DIVISOR = 100.0`,
`CALENDAR_ALPHA = 0.5`, `CALENDAR_CAP = 0.10`.

- **Points per match** `points_per_match(player)`:
  - stats assenti o `played_matches == 0` → stima FVM: `fvm / 100` (FVM è
    esposto già diviso per 1000; `fvm/100` è un'unità di punteggio
    plausibile per ruolo);
  - `played_matches >= 3` → `fanta_avg` (FM, include bonus/malus);
  - `0 < played_matches < 3` → media di `fanta_avg` e stima FVM.
- **Playing share** `playing_share(player, league)`: i minuti non esistono
  (KI-1), si usa la frazione di giornate giocate dalla squadra coperte da
  partite a voto: `min(1, played_matches / (current_matchweek - 1))`;
  a stagione non iniziata (o senza stats) → 1.0.
- **Expected remaining matches**:
  `playing_share × (SEASON_MATCHWEEKS - (current_matchweek - 1))`.
- **League context**: `LeagueContext { season, current_matchweek, teams,
  league_gf_per_match, league_ga_per_match }` con `TeamContext { team_id,
  team_name, gf_per_match: float | None, ga_per_match: float | None,
  upcoming_opponents: tuple[str, ...] }`. La forza squadra deriva dai match
  già giocati del calendario CSV (status ≠ 0): GF/GA a partita; nessun
  risultato → `None` (neutro). `current_matchweek` = max giornata giocata +
  1 (1 se nessuna giocata). `upcoming_opponents` = prossimi 5 avversari
  (matchweek > corrente). Le medie di lega sono calcolate sulle squadre con
  dati.
- **Calendar multiplier** `calendar_multiplier(player, league)`:
  - gruppi A e C: `mult = 1 + α × (media GF avversari − GF lega) / GF lega`;
  - gruppi D e P: `mult = 1 − α × (media GF avversari − GF lega) / GF lega`
    (la difesa è penalizzata dall'attacco avversario; GA lega ≡ GF lega);
  - dato assente per la squadra o per gli avversari → 1.0;
  - clamp a `[1 − CALENDAR_CAP, 1 + CALENDAR_CAP]`.
- **Total** `project(player, league) -> PlayerProjection`:
  `ppm × (multiplier × min(5, matches) + max(0, matches − 5))` — il
  moltiplicatore si applica solo alle prossime 5 giornate.

### Data mapping (layer data)

- `fetch_quotazioni.read_players` → `list[Player]` (CSV quotazioni; nuova
  colonna `team_id` per il join con il calendario).
- `fetch_stats.read_season_stats` → `dict[player_url, SeasonStats]`.
- `fetch_fixtures.read_league_context` → `LeagueContext` (CSV calendario).
- `attach_stats` per il merge prima della proiezione.

## Consequences

- Easier: entità e formule testabili in purezza senza rete né file; il
  modello funziona da subito (zero dati → stime FVM neutre) e migliora
  durante la stagione; una sola formula di proiezione condivisa da live e
  cache.
- Harder: senza minuti, la stima di presenza è grossolana (KI-1); il
  parametro `FVM_PPM_DIVISOR` è calibrato a mano e va rivisto se le stime
  risultano fuori scala; il calendario non considera rigori/xG (per
  miglioramenti futuri).
- Revisit later: sostituire la stima FVM con modello xG (Understat) quando
  le stats in corso superano la soglia; affinare α/cap con dati storici;
  aggiungere la classifica come fonte di forza squadra.

## Alternatives considered

- **Modello basato sui minuti reali (Understat):** rejected per M3 — fonte
  aggiuntiva, minuti assenti in Fantacalcio.it (KI-1); riusabile in seguito
  come cross-check.
- **Proiezione solo su stats in corso:** rejected — a inizio stagione tutte
  zero, l'ottimizzatore non avrebbe segnale.
- **Forza squadra da classifica esterna:** rejected — nuovo scraper per un
  dato derivabile dai risultati già scaricati (calendario CSV).
- **Multiplicatore calendario su tutta la stagione:** rejected — il piano
  (PLANNING §5) limita l'aggiustamento alle prossime 5 giornate.
