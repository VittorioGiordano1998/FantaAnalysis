# Task: Pagina "Guida asta" per squadra (replica struttura FantaLab)

- **ID:** M8-T9
- **Status:** Done
- **Date opened:** 2026-08-07
- **Date done:** 2026-08-07
- **Severity:** Medium
- **Area:** ui

## Problem

L'utente ha chiesto di ricreare nell'app una sezione uguale alla "Guida
Asta" di FantaLab (https://app.fantalab.it/guida-asta): selettore di
squadra e, per la squadra scelta, la rosa completa ordinata per ruolo con
prezzi e indicatori. Verificato che il contenuto premium di quella pagina
(formazione titolare, rigoristi, ballottaggi, prezzi consigliati) è
protetto da login (API `/guida` → 401): si ricrea la struttura con i dati
pubblici già presenti nell'app (listone QI/QA/FVM + ruoli Mantra + stats).

## Proposed Solution

- `pages/GuidaAsta.py` (layer ui, solo rendering/input):
  - selettore squadra (selectbox, compatibile mobile);
  - per la squadra scelta: roster raggruppata per gruppo ruolo
    (Portieri/Difensori/Centrocampisti/Attaccanti), ordinata per ruolo
    (ordine listone) poi QI decrescente poi nome, con colonne compatte:
    nome, ruoli Mantra, QI, QA, FVM, media voto, presenze, stato
    (libero/preso da ...);
  - marcatura dei giocatori già presi all'asta dallo stato (`state.py`),
    come il badge "preso" della guida FantaLab;
  - caption per gruppo: conteggio e QI totale.
- Nessuna modifica a `logic`/`data`: si riusano `get_players`,
  `get_state`, `taken_urls`, `ROLE_GROUP`, `GROUP_LABELS`.

## Notes

- Nessun ADR: nessun cambio di forma entità né di semantica del modello.
- Fonte dati: cache CSV esistenti (quotazioni + stats), non le API
  FantaLab (dati non pubblici per la guida premium).
- Il contenuto premium di FantaLab (formazione titolare, rigoristi,
  punizioni, corner, ballottaggi, rating allenatore, prezzi consigliati)
  resta escluso per mancanza di accesso pubblico.

## Resolution

- Nuova pagina `pages/GuidaAsta.py` (layer ui, solo rendering/input):
  selettore squadra (selectbox) e rosa completa della squadra raggruppata
  per gruppo ruolo (Portieri/Difensori/Centrocampisti/Attaccanti), ordinata
  per ruolo (ordine listone) → QI decrescente → nome, con colonne compatte:
  nome, ruoli Mantra, QI, QA, FVM, media voto, presenze, stato (libero o
  "Preso — <owner>" dallo stato asta). Header con totale giocatori e QI;
  caption per gruppo con conteggio e QI.
- Nessuna modifica a `logic`/`data`; dati dalle cache esistenti via
  `ui_common.get_players` + `state.get_state`.
- Verifica: `pytest` → 147/147; `ruff check` e `ruff format --check`
  puliti; smoke test su dati reali (494 giocatori, 20 squadre, gruppi
  ordinati correttamente). CHANGELOG aggiornato.
- Limitazione: il contenuto premium di FantaLab (formazione titolare,
  rigoristi, punizioni, corner, ballottaggi, rating allenatore, prezzi
  consigliati) resta escluso: API FantaLab `/guida` non pubblica (401).
