# ADR: Squad optimization model

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision-makers:** project owner

## Context

M4 implements the core of the app: the optimal squad recomputation among
remaining players (PLANNING §6) and the per-player spending limit (PLANNING
§2: "prezzo massimo consigliato = valore punti attesi − costo opportunità").
ADR-0001 already fixed the high-level approach (PuLP, maximize expected
points, budget/slots/remaining-only constraints, per-player spending limit);
this ADR freezes the precise semantics, constants and the spending-limit
definition. RULES require ADR approval for the optimization-model semantics.

Forces:

1. Performance: the base recompute must be ≤ 1 s; the spending limit is a
   per-player computation that must not block the auction flow.
2. Robustness: late-auction states (pool too small to fill slots, budget too
   low) must be explicit results, not exceptions.
3. Consistency: projections come from `projection.project` (ADR-0002) — the
   optimizer never computes points itself.

## Decision

### Constants (`optimize.py`, layer logic)

- `DEFAULT_BUDGET = 500` (crediti, QI in Fantacalcio units).
- `ROSA_SLOTS = {RoleGroup.P: 2, RoleGroup.D: 8, RoleGroup.C: 8,
  RoleGroup.A: 7}` (25 giocatori).
- `PRICE_FIELDS = ("qi", "qa")`; prezzo = QI per default, QA opzionale con
  fallback a QI quando assente; prezzo `None` → 0.

### Base model `optimize_squad(players, league, budget, slots, taken_urls, price_field)`

- Pool = giocatori con `url` non in `taken_urls` (solo rimasti all'asta).
- Punti per giocatore = `project(p, league).total_points` (ADR-0002).
- Binario `x_p` per ogni giocatore del pool (variabili nominate `x_<idx>`;
  gli URL non sono nomi validi per CBC).
- Obiettivo: massimizzare `Σ punti_p · x_p`.
- Vincoli:
  - budget: `Σ prezzo_p · x_p ≤ budget`;
  - slot per gruppo: `Σ x_p (gruppo g) == slot_g` (uguaglianze esatte:
    la rosa finale è completa).
- Risultato `SquadResult { selected (tupla in ordine di pool), total_points,
  total_cost, budget, status }`; `status` = `"Optimal"` | `"Infeasible"`
  (pool insufficiente a coprire gli slot o budget irrealizzabile → risultato
  esplicito, mai eccezioni).

### Spending limit `spending_limit(player, players, league, ...)`

Il prezzo massimo da offrire per `player` è il più grande prezzo a cui
comprare `player` non peggiora la rosa ottimale finale:

- **Baseline** `P0`:
  - se `player ∈ S*` (rosa ottimale di base sul pool completo): `P0` =
    ottimo sul pool *senza* `player` (un solve);
  - altrimenti: `P0 = P*` (l'ottimo di base; togliere un non selezionato
    non cambia l'ottimo).
- **Forced points** `Q(pr)`: ottimo del modello di base con vincolo
  aggiuntivo `x_player = 1` e budget `B − pr` (il prezzo di `player` esce
  dal budget). `Q` è non crescente in `pr`; forced infeasible → −∞.
- **Max price** `m = max { pr ∈ [0, B] interi | Q(pr) ≥ P0 }`, trovato con
  binary search monotono (~log2(B+1) solve):
  - `Q(B) ≥ P0` → `m = B` (indispensabile a qualsiasi prezzo);
  - `Q(0) < P0` → `m = 0` (da non comprare: il giocatore non è nella rosa
    ottimale nemmeno gratis);
  - altrimenti il più grande `pr` con `Q(pr) ≥ P0`.
- `SpendingLimit { player_url, max_price, baseline_points, forced_points,
  status }`.

### Caching (ui layer, M4-T3)

- `@st.cache_data` sulla composizione "carica dati → proiezioni → solve",
  chiave = snapshot dell'input (flag aggiornamento; a M5 si aggiungono
  giocatori presi/budget/slot da `state.py`).
- Il modello PuLP è ricostruito solo per chiavi nuove; il solve di base è
  unico per snapshot.

## Consequences

- Easier: semantica precisa e testabile (determinismo CBC); la rosa ottimale
  si ricalcola in ~tensina di ms (target ≤ 1 s ampiamente rispettato);
  il limite di spesa ha un significato operativo chiaro ("sopra questo
  prezzo la tua rosa finale peggiora").
- Harder: il limite di spesa costa ~log2(B) solve per giocatore
  (~100-300 ms): va mostrato on-demand o cachato per snapshot, non
  ricalcolato a ogni interazione; il confronto `Q(pr) ≥ P0` è in punti
  reali, quindi per i non selezionati risponde spesso 0 (il giocatore non
  è mai conveniente) — la UI dovrà mostrarlo con chiarezza (non è un bug).
- Revisit later: alternativa esatta a costo fisso via dual LP relaxation;
  mostrare anche il "valore equo" (punti/λ) come metrica secondaria;
  tollerare slot incompleti (rosa parziale) se l'asta si chiude con ruoli
  mancanti.

## Alternatives considered

- **Limite = credito equivalente `punti/λ`** (λ = punti per credito
  all'ottimo): rejected — ignora il costo opportunità dei ruoli mancanti
  che PLANNING §2 richiede esplicitamente.
- **Shadow price del vincolo budget (dual LP):** rejected — non esatto per
  MIP, difficile da spiegare all'utente.
- **Forced solve a prezzo corrente con aggiustamento lineare:** rejected —
  approssimazione senza il controllo di monotonia del binary search.
- **Rosa parziale (slot `≤`) invece di uguaglianza:** rejected — la rosa
  finale è per regolamento completa; l'infeasibility va segnalata, non
  nascosta.
