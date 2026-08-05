---
description: Create a task file from the task template
argument-hint: <Name>
---

# /new-task <Name>

Create a work item in `docs/project/tasks/<Name>.md` from `TASK_TEMPLATE.md`. Used at the start
of any non-trivial work so the work is tracked before it is executed.

## Usage

```
/new-task M1-T2-Scraper-quotazioni-con-cache-CSV
```

## Output

1. `docs/project/tasks/<Name>.md` populated from `TASK_TEMPLATE.md`:
   - `# Task: <Name>`
   - `ID` (optional `TASK-<N>` or milestone code)
   - `Status: Proposed`
   - `Date opened: <today>`
   - `Severity` and `Area` filled when known
   - `Problem`, `Proposed Solution`, `Notes`, `Resolution` sections

## Conventions

- ID: optional; use `TASK-<N>` (next free number) or a milestone code.
- Status starts at `Proposed`; move to `In Progress` when execution starts and `Done` when
  complete, filling `Resolution` and `Date done`.
- Follow the task-first workflow in `docs/agents/RULES.md`: create the task, execute it, and
  if it leaves unresolved problems behind, file a Known Issue with `/new-issue`.
