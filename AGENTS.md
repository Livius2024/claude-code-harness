# AGENTS.md — claude-code-harness

Rules for every coding agent working on this repository (Claude Code, Codex).

## What this repository is

The factory template for the owner's projects (Python apps for financial audit, RAG agents, MCP servers). `project-starter/` is copied into a project by `new-project.ps1` and never overwrites existing files. Files in it are written for the agents of that future project, so placeholders like `<project name>` stay.

## Commands

| Task | Command |
|---|---|
| Install | `uv sync` |
| Tests | `uv run pytest -q` |
| Type check | `uv run pyright` |
| Lint / format | `uv run ruff check . && uv run ruff format --check .` |
| Workflow lint | `actionlint .github/workflows/*.yml project-starter/.github/workflows/*.yml` |

CI (`.github/workflows/ci.yml`) runs all of them on every PR.

## Conventions

- The starter's scripts (`project-starter/scripts/`) use the standard library only: projects run them without installing anything.
- Every rule in a starter file that an agent must obey in a cloud thread is either in a `.claude/rules/*.md` file without `paths:`, in `AGENTS.md`, or enforced by a GitHub check. Path-scoped rules and hooks are local-only extras.
- Keep the starter's `AGENTS.md` under ~150 lines.
- A change to a gate (workflow, check script, `owner-approval-paths.txt`, `branch-protection.json`) comes with a test or an actionlint-clean workflow, and a line in `project-starter/docs/github-gates.md` if the owner's steps change.

## Safety

- Never push to `main`, force-push or rewrite history. Never commit secrets or the owner's local paths beyond those already documented in `README.md`.
- Never delete, skip or weaken a failing test.

## Code Review Rules

Codex reads this section when it reviews a pull request. Flag as **P0** or **P1**:

- **P0** A gate that can be bypassed: a check that passes when it should fail, a workflow whose required job can be skipped or replaced by a later run on the same SHA, a PR able to edit the rules that judge it.
- **P0** A secret or token in the diff.
- **P1** A starter rule that cloud threads would not load (only in a `paths:` rule or a hook) presented as enforced.
- **P1** A test deleted, skipped or loosened; a gate change without a test.
- **P1** `project-starter/scripts/` importing a non-standard-library package.
- **P1** `README.md` or `docs/github-gates.md` instructions that no longer match the files.
