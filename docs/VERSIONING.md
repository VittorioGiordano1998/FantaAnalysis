# Versioning

## Code

- SemVer: `MAJOR.MINOR.PATCH`.
- Pre-1.0 (`0.x.y`): MINOR may include breaking changes (per SemVer pre-1.0 convention).
- Post-1.0: breaking changes increment MAJOR.

## App

The Streamlit app version follows the SemVer tag (no versionCode; the deployed version is the
tag/branch on Streamlit Cloud).

## Docs

Docs share the same version as code. When code releases `v0.1.0`, docs are tagged at `v0.1.0`.

## CHANGELOG

`CHANGELOG.md` at repo root, Keep a Changelog format. The `Unreleased` section is appended via PRs.

## Breaking changes

A `BREAKING CHANGE` footer in a Conventional Commit triggers a major version bump in release
tooling.
