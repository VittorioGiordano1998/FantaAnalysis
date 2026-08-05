# ADRs — Architecture Decision Records

Each ADR records a decision that shapes the code in a way that is hard to reverse.

- [`ADR-0001-tech-stack-and-layers.md`](ADR-0001-tech-stack-and-layers.md) — Streamlit + PuLP,
  CSV cache, layer rules `ui → logic ← data`.

## Conventions

- One file per decision, numbered `ADR-<N>-<slug>.md` from `ADR_TEMPLATE.md`.
- Status: `Proposed` | `Accepted` | `Superseded by ADR-<N>`.
- Logic semantics (projection/optimization model, entity shapes) require an ADR before they can
  change (`docs/agents/RULES.md` §Never change domain logic without an ADR).
