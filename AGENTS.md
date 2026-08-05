# FantaOptimizer

This is the FantaOptimizer project: a Streamlit web app that tracks the Fantacalcio auction state
and recomputes the optimal squad among remaining players. See the docs for architecture,
contributing, and feature details.

## Quick links

- `PLANNING.md` — product plan (features, data sources, milestones).
- `docs/agents/RULES.md` — canonical rules for both Claude Code and opencode.
- `docs/project/architecture/overview.md` — system architecture.
- `docs/project/architecture/layers.md` — dependency rules (hard constraints).
- `docs/onboarding.md` — first-time contributor guide.
- `CONTRIBUTING.md` — commits, PRs, code style.

## Agent shortcuts

- `/new-page <Name>` — scaffold a Streamlit page under `pages/` + sidebar entry.
- `/new-task <Name>` — create a task file from `TASK_TEMPLATE.md`.
- `/new-issue <Title>` — create a `KI-<N>` known-issue file from `KNOWN_ISSUE_TEMPLATE.md`.
- `/new-dg <Title>` — create a `DG-<N>` delivery-gap file from `DELIVERY_GAP_TEMPLATE.md`.

## Workflow

**Task-first:** before executing non-trivial work, create the task record in
`docs/project/tasks/` (from `TASK_TEMPLATE.md` or `/new-task`); when done, close it with
`Status: Done` and a `Resolution`. File any unresolved problem as a Known Issue
(`docs/project/known_issues/`, `/new-issue`). See `docs/agents/RULES.md` §Task-first workflow.

## Rules

**`docs/agents/RULES.md` is the single source of truth — read it before changing code.**

Nothing is restated here. A second copy is a second thing to keep correct, and the copy is
what goes stale.
