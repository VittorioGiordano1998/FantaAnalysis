# Task: Consigli di acquisto in home e presa rapida Io/Avversario

- **ID:** M7-T2
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** ui | logic

## Problem

Durante l'asta l'utente deve scrivere ogni volta il nome della squadra che
prende e non ha uno strumento di consiglio in home: la sezione "Limite di
spesa" esiste ma è in `pages/RosaOttimale.py` e non è scopribile, e manca
una valutazione di utilità del giocatore (bisogno di ruolo, calendario
facile, sinergia con le prese già fatte).

## Proposed Solution

1. **Presa rapida** (home): "Squadra che prende" diventa `st.segmented_control`
   con solo la propria squadra (`state.own_team`) o "Avversario"; il prezzo
   si richiede solo per la propria squadra (owner salvato: `own_team` o
   `"Avversario"`).
2. **Nuovo `utility.py`** (layer logic, puro): mappatura preset modulo →
   conteggi `(P, D, C, A)` e `utility_score(player, league, slots_left,
   own_players, module)` → 0..1, media di tre componenti:
   - **slot_need**: bisogno di ruolo dagli slot residui vs quota attesa dal
     modulo (gruppo saturo → 0);
   - **calendar_ease**: frazione dei prossimi 5 avversari "facili" (per
     A/C la difesa avversaria sotto la media di lega; per D/P l'attacco);
   - **coverage**: per le settimane facili del giocatore, quanto aggiunge
     rispetto ai giocatori già presi della propria squadra.
   Espone anche `opponent_outlook(player, league)` (avversari con forza e
   flag facile) per la UI e i test.
3. **Sezione "Consigli di acquisto" in home**: selettore modulo, ricerca del
   giocatore tra i rimasti, pulsante "Calcola consiglio" → prezzo max
   consigliato (`spending_limit` esistente), % utilità con dettaglio delle
   tre componenti, punti attesi, avversari facili. Calcolo cachato
   (`@st.cache_data`, chiave = snapshot asta + modulo + giocatore + refresh).

## Notes

- Il modulo agisce solo sui pesi della % utilità; gli slot di rosa di lega
  (2P-8D-8C-7A) restano invariati per stato asta e ottimizzatore.
- Nuove funzioni pure in `logic`: nessun ADR necessario (forma delle entità
  e semantica projection/optimize invariate).
- Le prese esistenti con nomi arbitrari restano compatibili (solo lettura).

## Resolution

- `main.py` "Prendi giocatore": `st.text_input` → `st.segmented_control`
  con `[own_team, "Avversario"]` (default: propria squadra); prezzo richiesto
  solo per la propria squadra; `OWNER_OTHER = "Avversario"` come costante.
- Nuovo `utility.py` (logic, puro): `MODULES` (4 preset → `(P, D, C, A)`),
  `opponent_outlook` (avversari con forza e flag facile per ruolo) e
  `utility_score` (media di slot_need, calendar_ease, coverage, ciascuna
  0..1; neutro 0.5 quando mancano i dati).
- `main.py` nuova sezione "Consigli di acquisto" in home: selettore modulo,
  ricerca tra i rimasti, "Calcola consiglio" → prezzo max
  (`spending_limit`), % utilità con dettaglio componenti, punti attesi,
  avversari facili. Calcolo cachato con `@st.cache_data` (`_advice_for`,
  chiave = snapshot asta + modulo + giocatore + refresh).
- 12 nuovi test unitari in `tests/test_utility.py` (mapping modulo, slot
  saturi/chiusi/scoperti, frazione avversari facili, copertura neutra/penalizzata/piena,
  outlook con flag e forza, benchmark difensori). Il modulo agisce solo sui
  pesi dell'utilità: slot di rosa di lega e ottimizzatore invariati.
- Verifica: `pytest` → 87/87 passati; `ruff check .` pulito; smoke test
  AppTest: 3 pagine OK, consiglio calcolato su dati reali (es. Martinez L.
  → max 39 crediti, utilità 17%), segmented Io/Avversario mostra/nasconde
  il prezzo.
