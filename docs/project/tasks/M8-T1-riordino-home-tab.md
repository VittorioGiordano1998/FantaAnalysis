# Task: Riordino home con tab e formazione disegnata per modulo

- **ID:** M8-T1
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** ui | logic

## Problem

La home è un unico scroll con 6 sezioni (stato asta, consigli, copertura,
listone, bottoni). L'utente vuole una schermata principale ridotta a:
presa giocatori (Io/Avversario), formazione con i propri presi disegnata
sul modulo (4-3-3, 4-4-2, …) per vedere quanti mancano per posizione, e
una tab di suggerimenti con la ricerca del giocatore chiamato.

## Proposed Solution

- Sidebar: "Aggiorna dati" (spostato dalla home) + esporta/importa stato +
  report.
- `main.py` a tab: "Asta" (budget, prendi giocatore, annulla presa,
  selettore modulo + formazione disegnata a righe Portiere/Difensori/
  Centrocampisti/Attaccanti con slot pieni/vuoti, contatori rosa per
  ruolo, tabella Prese), "Suggerimenti" (consigli con ricerca giocatore +
  copertura giornate facili), "Listone" (quotazioni).
- Modulo unico in `st.session_state` (chiave `"modulo"`): scelto in tab
  Asta, usato anche dai consigli; cambiabile ad asta in corso — il
  ricalcolo è automatico perché `_advice_for` ha `module` nella chiave
  cache e la formazione si ridisegna a ogni rerun. La rosa di lega
  (2P-8D-8C-7A) resta fissa.
- `utility.py`: `FormationLine` e `formation_lines(module, own_players)`
  (funzione pura: righe del modulo riempite con i propri presi in ordine di
  presa, troncate ai conteggi di modulo).

## Notes

- Nessun ADR: nuove funzioni pure; nessuna modifica a entità esistenti.

## Resolution

- `main.py` riorganizzata a tab: "Asta" (budget, prendi giocatore con
  Io/Avversario, annulla presa, selettore modulo + formazione disegnata a
  righe per gruppo con slot pieni/vuoti, contatori rosa per ruolo, tabella
  Prese), "Suggerimenti" (consigli con ricerca del giocatore chiamato +
  copertura giornate facili), "Listone" (quotazioni).
- Sidebar: "Aggiorna dati" spostato dalla home + esporta/importa + report.
- Modulo unico in `st.session_state["modulo"]` (default 4-3-3), scelto in
  tab Asta, letto anche dai consigli (caption "Modulo: X — cambialo in tab
  Asta"); cambiabile ad asta in corso: il consiglio si ricalcola perché
  `_advice_for` ha `module` nella chiave cache, la formazione si ridisegna
  a ogni rerun. Rosa di lega 2P-8D-8C-7A invariata.
- `utility.py`: `FormationLine` + `formation_lines(module, own_players)`
  (righe del modulo riempite con i propri presi in ordine di presa,
  troncate ai conteggi di modulo).
- 3 nuovi test di `formation_lines` (riempimento per gruppo/modulo, modulo
  diverso, rosa vuota).
- Verifica: `pytest` → 109/109 (venv locale e con dipendenze attuali);
  `ruff check` + `ruff format --check` puliti; smoke AppTest: 3 tab
  presenti, cambio modulo 4-3-3 → 3-5-2 senza eccezioni.
