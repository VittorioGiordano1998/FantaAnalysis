# Known Issue: Minuti giocati non disponibili da Fantacalcio.it

- **ID:** KI-1
- **Status:** Open
- **Date opened:** 2026-08-05
- **Date fixed:**
- **Severity:** Medium
- **Area:** data

## Symptom

Il modello di proiezione (PLANNING §5) prevede "minuti giocati" tra le basi
delle proiezioni punti, ma nessuno dei dati estratti dagli scraper espone i
minuti: `fetch_stats` (colonna `played_matches` = partite a voto, non minuti)
e `fetch_fixtures` non contengono il dato.

## Root cause

Verificato per ispezione il 2026-08-05 su Fantacalcio.it:

- pagina lista `/statistiche-serie-a`: colonne PV, MV, FM, Gol, GS, Rig, RP,
  Ass, Amm, Esp — nessun "Minuti";
- pagina giocatore `/serie-a/squadre/<team>/<slug>/<id>` (anche stagioni
  passate, es. 2025/26): sezioni `#player-summary-stats`,
  `#player-season-table` (titolare/entrato/squalificato/infortunato/
  inutilizzato), grafi voto/fantavoto/bonus per giornata — nessun "Minuti".

## Attempted fixes

- Ricerca su pagina lista e pagina giocatore di etichette/valori "minuti":
  assenti.
- Pagina calendario stagioni passate: non fruibile (`/calendario/1/2025-26`
  redirige al dettaglio partita).

## Fix direction

Due opzioni valutabili a M3 (proiezioni):

1. Stimare i minuti dalle partite a voto e dai grafi per giornata
   (titolare ≈ 90', entrato ≈ 45') — approssimazione senza rete aggiuntiva;
2. aggiungere Understat come fonte minuti (già pianificato per il
   cross-check xG/xA in PLANNING §3) — dati precisi, costo di un altro
   scraper.

## Notes

- Impatto: solo la componente "minuti" della proiezione è da approssimare;
  il resto delle stats è completo.
- Related: M2-T1 (stats), M3 (proiezioni).
