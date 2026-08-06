# Task: Schermata unica — chi prendere per coprire le partite facili

- **ID:** M8-T8
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** ui | logic

## Problem

La home ha tre tab (Asta/Suggerimenti/Listone) con molte sezioni.
L'utente vuole UNA sola schermata: cerchi un calciatore e l'app dice solo
chi altro prendere per avere le partite facili coperte.

## Proposed Solution

- `guide.py`: `coverage_completion(player, players, ...)` — greedy che
  parte dalle giornate facili del giocatore cercato e aggiunge a ogni
  passo il rimasto (escluso il cercato) che copre più giornate non ancora
  coperte (a parità punti, poi costo); si ferma a copertura completa o
  quando nessuno aggiunge più nulla.
- `main.py`: riscritta a schermata unica — via tab e sezioni (stato asta,
  consigli, copertura, listone, formazione); resta la sidebar (versione,
  aggiorna dati, export/import, report) e la nuova feature: ricerca
  calciatore → partite facili sue + tabella "prendi questi" (nome,
  squadra, ruoli, QI, punti, giornate aggiunte, coperte cumulative,
  costo) + riepilogo e scoperte residue. Calcolo cachato per
  giocatore+prese.
- Test: `coverage_completion` (esclusione del cercato, ordine greedy,
  stop senza aggiunte, limit), smoke delle pagine invariato.

## Notes

- Le pagine laterali (RosaOttimale, Analisi, Guide) restano; cambia solo
  la schermata principale.

## Resolution

- `guide.py`: `coverage_completion(player, players, ..., limit=12)` —
  greedy che parte dalle giornate facili del cercato ed esclude il cercato
  dal pool; a ogni passo aggiunge chi copre più giornate non ancora
  coperte (a parità punti, poi costo); si ferma a copertura completa,
  quando nessuno aggiunge nulla o al limite.
- `main.py` riscritta a schermata unica: rimosse le tab Asta/Suggerimenti/
  Listone e tutte le sezioni associate (presa, formazione, consigli,
  copertura, listone, modulo); restano sidebar (versione, aggiorna dati,
  export/import, report) e la nuova feature "Copertura partite facili":
  ricerca calciatore (selectbox ricercabile) → partite facili sue, messaggio
  "con X copri a/N: prendendo questi arrivi a b/N", tabella dei suggerimenti
  (nome, squadra, ruoli, QI, punti, giornate aggiunte, coperte cumulative,
  costo) e giornate ancora scoperte. Calcolo cachato (`_completion`, chiave
  = giocatore + prese + refresh).
- 4 test nuovi su `coverage_completion` (partenza dalle settimane del
  cercato, esclusione del cercato, stop senza aggiunte, limit).
- Verifica: `pytest` → 135/135; ruff puliti; smoke AppTest: 0 tab, 494
  giocatori ricercabili, Martinez L. → 24/38 coperti da solo, con Esposito
  Se. e Hojlund si arriva a 38/38.

## Follow-up (stessa schermata)

- `guide.coverage_completion` accetta `budget` (crediti massimi; salta i
  giocatori che non ci stanno) e `excluded` (URL da escludere); nuova
  `coverage_completions(..., k=5)` → alternative di copertura multiple
  (ognuna esclude i suggeriti delle precedenti).
- `main.py`: input "Budget massimo per i suggerimenti" (default: residuo
  dello stato asta, nella chiave cache), 5 alternative in expander con
  riepilogo e tabelle, caption "QI di X: N crediti (prezzo consigliato)".
- Test: budget (stop a budget esaurito, salta inaccessibili, preferisce il
  più economico a parità), `excluded`, alternative multiple senza
  sovrapposizioni.
- Verifica: `pytest` → 139/139; smoke: Martinez → 5 alternative
  42→30 crediti tutte 38/38; con budget 40 le alternative si adattano.

## Follow-up 2 (stessa schermata)

- `guide.coverage_completion(..., same_role=True)`: per default il pool è
  filtrato a chi condivide almeno un ruolo con il cercato (multiruolo
  incluso) — se cerco una W non compaiono DC.
- `main.py`: visibile solo l'**Alternativa principale**; le altre si
  rivelano con la checkbox "Mostra tutte le alternative" (default spenta,
  con nota); rendering estratto in `_render_alternative`.
- Test: filtro per ruolo (stesso ruolo → pool ristretto; `same_role=False`
  → tutti), multiruolo condiviso (W/A accetta giocatori con ruolo A),
  alternative multiple nello stesso ruolo.
- Verifica: `pytest` → 141/141; smoke: Martinez (PC) → solo suggeriti PC,
  una sola alternativa visibile, 4 expander dopo la spunta.
