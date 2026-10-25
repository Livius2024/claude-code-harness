# AGENTS.md — <project name>

<!-- starter:unfilled -->

Shared rules for every coding agent in this repository (Claude Code, Codex, others).
Keep it under ~150 lines. Put here only what an agent cannot learn by reading the code.

## First session (delete this section when done)

This file was copied from the project starter. Before any other work (exception: if the owner starts with `/autopilot`, skip this section until that run ends, then do it from Autopilot's end-of-run proposals):

1. Read the repo (package.json, pyproject.toml, README, folder layout) and fill every `<...>` below with what you find.
2. Ask the owner, one question at a time with a recommended answer, only what the repo cannot tell you: what the project is for, who uses it, which domain rules apply.
3. If the real check commands exist, copy `.claude/verify.example.json` to `.claude/verify.json` and put them in it. If there is no code yet, leave it; the verify gate auto-detects later.
4. Delete the rules in `.claude/rules/` that don't apply to this stack.
5. Ask the owner for the Non-negotiables (what must never break) and write each with its check.
6. Remove the `starter:unfilled` marker and this section.

## What this project is

<One paragraph: what it does, who uses it, what matters most: correct numbers, speed, or look.>

## Commands

| Task | Command |
|---|---|
| Install | `<npm install / uv sync>` |
| Dev server | `<npm run dev>` (port <3000>) |
| Tests | `<npm test / uv run pytest>` |
| Type check | `<npm run typecheck / uv run pyright>` |
| Lint / format | `<npm run lint / uv run ruff check .>` |
| Build | `<npm run build>` |
| DB migration | `<npm run db:generate && npm run db:migrate>` |

Run the narrowest relevant check after each change, and the full set before calling work done.
CI (`.github/workflows/ci.yml`) runs the same commands on every PR and is the gate that decides the merge. Locally, the same commands also go in `.claude/verify.json` for Claude Code's verify gate.

## Layout

- `<src/app>`: <routes / pages>
- `<src/lib>`: <domain logic>
- `<tests>`: <where tests live and how they are named>

## Conventions

- Match the existing style; make the smallest change that fully solves the request.
- No new dependencies, abstractions or config options unless the task needs them.
- Domain vocabulary is in `GLOSSARY.md`, decisions in `docs/adr/`, the visual system in `DESIGN.md`. Use those terms in code and follow them in UI.
- Rules longer than a few lines go in `docs/<topic>.md` and are linked from here, so this file stays an index that fits in context.

## Planning and autonomy

Two phases, with different rules.

**Before `spec.md` and `plan.md` are approved by the owner:** ask, one question at a time, with a recommended answer. Never assume domain rules, product behaviour, data shape, or anything that costs money. Read the repo first; ask only what it cannot tell you. Work bigger than one sitting goes through spec → tickets → implement (local tickets in `.scratch/<feature>/`).

**After they are approved:** do not ask again about anything inside them. Choose libraries, file layout, naming, error messages and other routine technical details yourself, inside the approved stack. Implement, test, debug, fix and re-test without checking in. Commit on the feature branch as you go when the approved `plan.md` says commits are allowed (the owner's default for autonomous work); otherwise leave the changes uncommitted and say so.

Stop and ask only for: a contradiction between the plan and what you find in the code or the environment; missing access (API key, account, service) or anything that costs money; a change to domain, security, schema, migration or payment rules; a check you cannot run (say which, and why).

Repair budget: 3 attempts per failing check. When it is spent, report **BLOCAT** with the diagnosis; do not lower the bar. A check that did not run is **NEVERIFICAT**, never a pass.

## Shared files and roles

- `spec.md` (what, for whom, non-goals, domain rules) and `plan.md` (architecture, stack, order of work) are approved by the owner and are the contract.
- Requirements manifest: the `## Requirements` section of `spec.md`, one item per requirement, `- R1: <owner's words>`. IDs are never reused or renumbered; a dropped requirement stays listed as `- R7: (dropped <date>) ...` with its row marked in Evidence.
- `ACCEPTANCE.md`: exactly one row per manifest ID (CI's `acceptance` check fails otherwise), ID → requirement in the owner's words → verifiable criterion → command or scenario → status (PASS / FAIL / NEVERIFICAT / BLOCAT) → SHA → evidence path. A row without a command or scenario can never be PASS. Status changes only with the command's real result on the current SHA.
- `HANDOFF.md`: state at a pause (what is done, what is next, open questions).
- Roles when both engines work on the repo: Claude Code builds and decides; Codex reviews, tests, debugs and fixes what the brief names. The checker reads the diff, `spec.md`, `plan.md` and `ACCEPTANCE.md` and runs the commands itself; it never trusts the builder's summary. After a fix by one engine, the other re-checks the same SHA. Nobody rewrites `spec.md` or relaxes an acceptance row to make a result look green.
- Use sub-agents for research and for independent tickets that can run in parallel.
- **If the owner runs `/autopilot` here:** that command replaces the spec → tickets → implement flow for the run. Autopilot's manifest and spec in `.autopilot/` stand in for `spec.md`/`plan.md`, its final blind acceptance stands in for `ACCEPTANCE.md` rows (copy the verdicts into `ACCEPTANCE.md` when the run ends), and its per-ticket commits are authorized by the command. Autopilot does not edit this file; accept or reject its end-of-run proposals yourself. Start it only on a clean working tree, never with a real `.env` in its acceptance clone, and keep Romanian for the owner and English in code.

## Domain rules (never invent)

<Accounting, tax, audit, legal or payment rules this project encodes, each with its source (law, standard, the owner's instruction). If a rule is missing or ambiguous, stop and ask the owner; do not guess.>

## Non-negotiables

What this product must always do or never do, whatever the speed or cost trade-off. Each rule names the check that proves it holds (a test committed to git, a command, a release check), so an agent cannot skip it. The `direction` skill reports any rule without a check.

| Rule | Check |
|---|---|
| <e.g. A user only ever sees their own company's data> | <`tests/access.test.ts`> |
| <e.g. Totals match the 1C balance to the cent> | <`uv run pytest tests/test_totals.py`> |

## Database

- Every schema change goes through a generated migration that is committed. Never push a schema straight to a database.
- <ID convention, e.g. random UUIDs for all non-auth tables.>
- Never run migrations against production; the owner does that.

## Safety

- Never commit secrets; never edit `.env*` unless asked (`.env.example` is the exception: names only, never a value). Never touch production data.
- No force-push, history rewrite, `reset --hard`, or push to `main`. Everything reaches `main` through a PR with green required checks.
- The `owner-approved` label:
  - **Owner only** on domain paths: `spec.md`, `plan.md`, `CLAUDE.md`, `docs/domain/**`, tax, fiscal and audit-rule files.
  - **You may add it** when every protected path in the PR is a factory path (`.github/**`, `.claude/**`, `AGENTS.md`, `scripts/check_*.py`, `scripts/browser_qa_comment.py`, the e2e guard files `e2e/fixtures.ts`, `e2e/server-log.ts`, `e2e/playwright.config.ts`, `e2e/guard-selftest/**`), CI is green and Codex has no open P0/P1.
  - Never when the PR removes a path from `.github/owner-approval-paths.txt` or weakens a check.
- Never edit `.github/owner-approval-paths.txt`, CI, branch protection or the check scripts to get a PR through.
- Never delete, skip or weaken a failing test to make the suite pass. Fix the code, or report why you can't.
- Never assume a change works: test it. If the project has no way to test it, ask the owner whether to skip testing.

## Definition of done

1. The requested behaviour works, shown by a check that actually ran (test, build, browser).
2. Type check and lint pass.
3. For UI: the page was checked in a browser at desktop and phone width.
4. The affected `ACCEPTANCE.md` rows are PASS on the current SHA, with the evidence path filled in.
5. A review by the other engine ran on the final change: on GitHub, Codex's automatic PR review (rules below); findings P0/P1 are fixed or explicitly accepted by the owner, and their conversations resolved. In an `/autopilot` run, Autopilot's blind acceptance is that independent check; a Codex review on top only if the owner asks.
6. The required checks are green on the PR's last commit and the PR is merged (squash). The merge is done by auto-merge where branch protection exists, otherwise by you, only on green (`.claude/rules/factory.md` step 5). A PR touching a domain path waits for the owner's `owner-approved` label.
7. The report says what changed, which checks ran, and what is still unverified.

## Code Review Rules

Codex reads this section when it reviews a pull request. Flag as **P0** or **P1** (anything below is optional):

- **P0** A number, rate, account code, legal reference or tax/audit rule that does not come from `spec.md`, `GLOSSARY.md`, `docs/domain/` or a source cited in the code. Money computed with floats instead of `Decimal` (Python) or integer minor units.
- **P0** A secret, token or real personal/client data in the diff; a `.env` file other than `.env.example`.
- **P0** A test deleted, skipped (`skip`, `xfail`, `.only`, `xit`) or loosened, a CI step, required check or `.github/owner-approval-paths.txt` weakened, or an `ACCEPTANCE.md` criterion relaxed, in order to make something pass.
- **P1** The PR does something no requirement in its `Requirements:` line asks for, or misses part of one (compare with `spec.md` and the linked issue). Flag drift from `plan.md` (stack, architecture, layout) too.
- **P1** An `ACCEPTANCE.md` row set to PASS without a command that exercises the requirement, without this PR's SHA, or with evidence that does not show the result.
- **P1** A browser check that imports from `@playwright/test` instead of `e2e/fixtures.ts`, weakens the guard in `e2e/fixtures.ts`, or widens `allowedHttpErrors`/`SERVER_LOG_ERRORS` beyond the failure it expects; a check of a requirement that saves or changes data that asserts only the screen, not the stored result (API or database).
- **P1** New behaviour without a test that would fail if it broke; tests that only mirror the code's own output for money or tax values.
- **P1** A schema change without a committed migration; a query or migration aimed at production.
- **P1** User input reaching SQL, shell, file paths or HTML unescaped; a missing access check on another user's or company's data.

Do not flag style the linters already enforce.
