# Onboarding

Welcome to FantaOptimizer! This guide gets you from zero to first contribution.

## Prerequisites

1. Python 3.11+ (`python --version` should print 3.11 or newer).
2. A GitHub account with access to the repo.

## Setup

1. Clone the repository.
2. Create a virtualenv: `python -m venv .venv` and activate it.
3. Install dependencies: `pip install -r requirements.txt`.
4. Verify the app starts: `streamlit run main.py`.

No local lint/test toolchain is required: `ruff` and `pytest` run on GitHub Actions at push/PR
time (`.github/workflows/ci.yml`). To run them locally, install `requirements-dev.txt`
(`pip install -r requirements-dev.txt`).

## First task

1. Read `docs/agents/RULES.md`.
2. Pick your agentic tool (Claude Code or opencode).
3. Create the task record:
   - `/new-task <Name>` in either tool.
4. Implement the module/feature described in `PLANNING.md` §10 for the current milestone
   (`docs/project/ROADMAP.md`).
5. Update `CHANGELOG.md` (Unreleased section) and any docs affected.
6. Push the branch and open a PR following the template; CI verifies lint, format and tests.

## Next steps

- Read `docs/project/architecture/overview.md` for the big picture.
- Read `docs/project/ROADMAP.md` for the milestone plan.
- Pick an open task in `docs/project/tasks/`.

## Questions?

Open an issue with label `question` or ping the team.
