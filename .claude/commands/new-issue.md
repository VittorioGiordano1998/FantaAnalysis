---
description: Create a known-issue file from the issue template
argument-hint: <Title>
---

# /new-issue <Title>

Create a defect record in `docs/project/known_issues/KI-<N>-<slug>.md` from
`KNOWN_ISSUE_TEMPLATE.md`. File it when a problem is observed or confirmed and no tracked issue
covers it yet.

## Usage

```
/new-issue Prezzo suggerito non aggiornato dopo la presa di un giocatore
```

## Output

1. `docs/project/known_issues/KI-<N>-<slug>.md` populated from `KNOWN_ISSUE_TEMPLATE.md`:
   - `ID: KI-<N>` where `<N>` is the next free number after the highest existing `KI-<N>` file
   - `Status: Open`
   - `Date opened: <today>`
   - `Severity` and `Area` filled when known
   - `Symptom`, `Root cause`, `Fix direction`, `Notes` sections

## Conventions

- Slug: kebab-case short form of the title.
- Follow the task-first workflow in `docs/agents/RULES.md`: file the issue when a task leaves an
  unresolved problem behind, or when a defect is observed independently of a task.
- When the defect relates to a delivery gap, add a `Related:` link to the `DG-<N>.md` file in
  `docs/project/delivery_gap/`.
