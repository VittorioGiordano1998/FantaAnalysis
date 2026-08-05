# ADR: Auction state model

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision-makers:** project owner

## Context

M5 introduces the live auction state: which players have been taken (mine
and other teams'), how much budget I have left, and which roster slots are
still open (PLANNING §2 #1/#5). Two forces shape the decision:

1. Streamlit Cloud has no persistent disk (ADR-0001): the state must
   round-trip through export/import bytes; `data/asta.json` is a local
   convenience only.
2. The optimizer (ADR-0003) consumes the state as (taken_urls, remaining
   budget, remaining slots): the state shape must map 1:1 onto those inputs.

## Decision

### Entities (`entities.py`, layer logic)

- `TakenPick { player_url: str, owner: str, price: int | None }` — a player
  taken at the auction, by whom, and (for my picks) at what price. `price`
  is `None` for other teams' picks (does not affect my budget).
- `AuctionState { budget: int, own_team: str = "Io", taken: tuple[
  TakenPick, ...] = () }` — `own_team` is the owner label that counts as
  "my" squad; `budget` is the total starting budget (default 500, from
  `optimize.DEFAULT_BUDGET`).
- Derived values are pure functions in `state.py`, not fields:
  - `taken_urls(state)` — URLs of all taken players (pool exclusion);
  - `spent_budget(state)` — sum of `price` over picks with `owner ==
    own_team` (None → 0);
  - `slots_remaining(state, players)` — `ROSA_SLOTS` minus my picks per
    `RoleGroup` (role resolved from `players` by URL; floored at 0).

### Persistence (`state.py`, layer data)

- `state.py` is the only module that reads/writes the auction-state JSON
  and performs import/export; `ui` never touches the file or the bytes
  directly.
- On-disk format (versioned, `version: 1`): `{ budget, own_team, taken:
  [[url, owner, price], ...] }`, UTF-8 JSON.
- `load_state(path)` returns `default_state()` when the file is missing;
  `save_state(state, path)` writes it; both default to `data/asta.json`.
- `export_state(state) -> bytes` / `import_state(bytes) -> AuctionState`:
  `import_state` raises `ValueError` on malformed payloads (bad JSON, wrong
  version, wrong shape), which the UI surfaces as an error message.
- Mutations are pure functions returning a new frozen state:
  `add_taken(state, pick)` (duplicate `player_url` → `ValueError`) and
  `remove_taken(state, player_url)`.

### UI (layer ui, M5-T2)

- The source of truth during a session is `st.session_state`; every
  mutation persists via `save_state` (local convenience) and the official
  Cloud path is export/import bytes.

## Consequences

- Easier: state maps 1:1 onto the optimizer inputs (taken_urls, budget,
  slots); persistence is versioned and testable without network; the UI
  stays thin (no file/JSON code in pages).
- Harder: other teams' picks have no price (only mine count against the
  budget); a pick without price can't be undone budget-wise after the fact
  (documented UI flow: always record the price for "Io").
- Revisit later: configurability of slots/budget per league (today fixed to
  ADR-0003 defaults), multiple "my" teams (co-op auction), pick timestamps.

## Alternatives considered

- **State as a plain dict in session_state:** rejected — no single source of
  truth for the shape, no validation, harder to test.
- **One JSON file per owner (mine/others):** rejected — unnecessary
  complexity; the owner field already separates them.
- **Store derived counters (spent, slots) in the JSON:** rejected — they are
  derivable from `taken` + `players`; storing them invites drift.
