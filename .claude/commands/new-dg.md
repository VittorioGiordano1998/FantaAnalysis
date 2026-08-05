---
description: Create a delivery-gap file from the gap template
argument-hint: <Title>
---

# /new-dg <Title>

Create a delivery-gap record in `docs/project/delivery_gap/DG-<N>-<slug>.md` from
`DELIVERY_GAP_TEMPLATE.md`. Use it for gaps that are not defects in a completed feature but
currently prevent release or make defects easier to ship unnoticed (missing milestone work,
missing CI, missing configuration, etc.).

## Usage

```
/new-dg Nessun check automatico delle regole di layer
```

## Output

1. `docs/project/delivery_gap/DG-<N>-<slug>.md` populated from `DELIVERY_GAP_TEMPLATE.md`:
   - `ID: DG-<N>` where `<N>` is the next free number after the highest existing `DG-<N>` file
   - `Status: Open` (or `Planned` when it tracks scheduled milestone work)
   - `Release impact` filled when known
   - `Description`, `Notes` sections

## Conventions

- Slug: kebab-case short form of the title.
- When the gap relates to specific defects, mention the `KI-<N>.md` files in `Notes`; the
  corresponding KIs link back to this gap from their own `Notes`.
- Gaps that derive from audit findings rather than a specific defect carry a
  "No related KI" note.
