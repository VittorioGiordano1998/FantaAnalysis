# Task: Multi-ruolo Mantra (parser, entità, formazione, listone)

- **ID:** M8-T3
- **Status:** Done
- **Date opened:** 2026-08-06
- **Date done:** 2026-08-06
- **Severity:** Medium
- **Area:** data | logic | ui

## Problem

I giocatori del listone hanno più ruoli Mantra (es. `m,c`, `pc,a`, `w,a`)
ma il parser salva solo il primo (`select_one` sul pill): il multiruolo si
perde e la formazione a posizioni vincolanti non può usare un `w,a` come
attaccante.

## Proposed Solution

- ADR-0005: `Player.roles: tuple[Role, ...] = ()` (ruolo primario
  invariato per gruppo rosa/proiezioni/ottimizzatore).
- `fetch_quotazioni`: parser multi-span, colonna CSV `roles`, read tollera
  cache vecchia; `read_players` mappa `roles`.
- `utility.formation_positions`: match per ruolo richiesto ∈ `player.roles`
  (fallback a `(role,)`).
- UI: formazione e listone mostrano i codici multiruolo (es. "E/W",
  "M/C").
- Test: parser multiruolo (Dimarco e/w), mapping entità, match formazione
  con `w,a` in posizione `a`, round-trip CSV, cache vecchia senza `roles`.

## Notes

- AdR-0005 documenta la semantica e i limiti (gruppo rosa dal ruolo
  primario).

## Resolution

- ADR-0005-multiruolo-mantra: `Player.roles: tuple[Role, ...] = ()`
  (ruolo primario invariato per gruppo rosa/proiezioni/ottimizzatore).
- `fetch_quotazioni`: parser multi-span (`select` invece di `select_one` su
  `span.role-mantra`), colonna CSV `roles` (codici separati da virgola),
  `read_quotazioni_csv` tollera la colonna assente (cache vecchia →
  `roles = role`); `read_players` mappa `roles`. Dalla fixture: 246
  giocatori multiruolo (es. Dimarco `e,w`, `m,c`, `t,a`, `w,a`).
- `utility.formation_positions`: match per ruolo richiesto ∈
  `player_roles(player)` (fallback `(role,)`) — un `w,a` copre una
  posizione `a`; `player_roles` esposta.
- `main.py`: formazione mostra i codici multiruolo (es. "E/W") nei posti
  occupati; listone mostra la colonna "Ruolo" con i codici (fallback a
  `role_label` per cache vecchia).
- Fix bug modulo: il widget era keyed e `st.rerun()` (conferma presa,
  aggiorna dati) interrompeva il run prima della creazione del widget →
  cleanup di Streamlit cancellava `session_state["modulo"]`. Ora il
  selectbox è senza key e il valore vive in una entry normale
  (`_module_selector`), sopravvive a qualsiasi rerun (verificato: presa
  confermata col modulo 3-5-2, il modulo resta 3-5-2 e Dimarco copre la
  posizione E).
- Test: parser multiruolo (Dimarco `e,w`, >100 multiruolo), mapping
  entità, fallback cache senza colonna `roles`, `player_roles`, match
  formazione multiruolo (posizione `a` coperta da `w,a`, nessun riuso).
- Verifica: `pytest` → 117/117; `ruff check` + `ruff format --check`
  puliti; smoke test end-to-end con fixture.
