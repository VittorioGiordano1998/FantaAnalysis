# ADR: Multi-ruolo Mantra dei giocatori

- **Status:** Accepted
- **Date:** 2026-08-06
- **Decision-makers:** project owner

## Context

Il listone Fantacalcio.it in modalità Mantra espone giocatori con più
ruoli (es. Dimarco: Esterno + Ala, codici `e`/`w`; molti `m,c`, `c,t`,
`w,a`, `ds,e`, `dd,dc`). Il parser salvava solo il primo ruolo
(`select_one` sul pill) e `Player.role` era un singolo `Role`: il
multiruolo si perdeva, e la formazione a posizioni vincolanti (M8-T2) non
poteva sapere che un `w,a` può coprire una posizione da attaccante.

## Decision

- `Player` (entities.py) guadagna `roles: tuple[Role, ...] = ()`:
  il campo `role` resta il ruolo primario (primo del pill) per
  compatibilità (gruppo rosa, proiezioni, ottimizzatore); `roles` è il
  multiruolo completo. `roles == ()` significa "solo `role`".
- `fetch_quotazioni.py`: il parser raccoglie TUTTI gli span
  `span.role-mantra` della riga; il CSV guadagna la colonna `roles`
  (codici separati da virgola, es. `e,w`); `read_quotazioni_csv` tollera
  la colonna assente (cache vecchia → `roles = role`).
- `utility.formation_positions`: una posizione è coperta se il ruolo
  richiesto appartiene a `player.roles` (con fallback a `(player.role,)`):
  un `w,a` può occupare una posizione `a`.
- Raggruppamento rosa (2P-8D-8C-7A), proiezioni e ottimizzatore continuano
  a usare il ruolo primario `role`.

## Consequences

- Più facile: la formazione riflette il multiruolo del listone; nessun
  cambio agli stati/proiezioni esistenti (campo opzionale con default).
- Più difficile: un multiruolo che attraversa gruppi (es. `w,a` = C e A)
  viene conteggiato in rosa col ruolo primario (w → C); la flessibilità di
  "dove lo schiero decide il gruppo" resta un miglioramento futuro.
- Revisitare: peso del multiruolo nello slot_need/utilità; scelta del
  ruolo d'uso per i calcoli.

## Alternatives considered

- **Multi-ruolo solo in UI (etichetta):** respinto — senza i dati
  nell'entità la formazione vincolante non può fare il match per ruolo.
- **`roles` come stringa:** respinto — tipizzazione debole; `tuple[Role]`
  è testabile e coerente con le entità esistenti.
