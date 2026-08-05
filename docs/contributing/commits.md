# Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/).

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

- `feat` — new feature
- `fix` — bug fix
- `refactor` — code change that neither fixes a bug nor adds a feature
- `perf` — performance improvement
- `docs` — documentation only
- `test` — adding or correcting tests
- `chore` — build, tooling, no production code change
- `build` — build system or external dependencies
- `ci` — CI configuration
- `style` — formatting, missing semicolons, etc.
- `revert` — revert a previous commit

## Scopes

`ui`, `data`, `scrape`, `projection`, `optimize`, `state`, `excel`, `docs`, `build`, `ci`.

## Examples

```
feat(optimize): maximize expected points with dynamic budget and slot constraints

fix(projection): weight clean sheets correctly for defenders

refactor(optimize)!: split SquadOptimizer into model and solver

BREAKING CHANGE: optimize_squad now takes a RosterSpec instead of loose arguments.
```

## Breaking changes

Use `!` after the type/scope and add a `BREAKING CHANGE:` footer. This triggers a major version
bump per SemVer.
