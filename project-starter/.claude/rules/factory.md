# Software factory rules (cloud threads)

This file has no `paths:` on purpose. Cloud threads in a claude.ai project load `CLAUDE.md`, `.claude/CLAUDE.md` and the root `.claude/rules/*.md` without `paths:` only. Hooks, `.claude/settings.json`, repo skills and `.mcp.json` do NOT run there, so every gate that matters lives in GitHub: CI, branch protection, auto-merge and Codex review (`docs/github-gates.md`). Roles and definitions are in `AGENTS.md`.

## The flow

1. **Contract first.** No feature code before the owner approved `spec.md` and `plan.md`. Interview with `mattpocock-skills:grill-with-docs`, then `to-spec`: one question at a time, with a recommended answer. Every requirement goes in the `## Requirements` section of `spec.md` as `- R<n>: <owner's words>`, and gets a row with the same ID in `ACCEPTANCE.md`. CI (`scripts/check_acceptance.py`) fails while any ID lacks its row.
2. **Tickets.** Split `plan.md` into GitHub issues (`to-tickets`), one per independently mergeable slice, each naming the R-IDs it covers. Independent issues run as parallel threads, one branch each.
3. **Build.** Test first (`mattpocock-skills:tdd`). One PR per issue; fill the PR template, including `Requirements: R…`.
4. **Check.** The required checks (`checks`, `acceptance`, `owner-approval`) must be green. Codex reviews every PR automatically: fix its findings or answer them on the thread, then resolve the conversation. A project with a web UI also gets `browser-qa`: browser checks with screenshots posted on the PR (`.claude/rules/browser-qa.md`). A bug you cannot fix in 3 attempts: comment `@codex fix <what is failing>` on the PR, then re-run the checks on its commit yourself.
5. **Merge.** Enable auto-merge (squash) on the PR; GitHub merges it when every required check is green. Never merge by hand, never bypass a required check.
6. **Owner gate.** A PR that changes a path in `.github/owner-approval-paths.txt` (domain rules: tax, accounting, audit, legal; the contract; the gates) fails `owner-approval` until the owner adds the `owner-approved` label. Never add that label yourself. Tell the owner in the thread, in Romanian, in one line, which files need their look.

## Never

- Never rewrite `spec.md` or relax an `ACCEPTANCE.md` criterion to make something pass. A requirement change is the owner's decision, asked once, then recorded in `spec.md` with the date.
- Never delete, skip or weaken a failing test, a CI step or a required check.
- Never push to `main`, force-push, or commit secrets. `.env.example` holds names only.
- Never call a check passed that did not run: it is **NEVERIFICAT**. After 3 failed repair attempts it is **BLOCAT**, with the diagnosis.

## Drift

Before opening a PR, compare the diff with the issue and the R-IDs it names. Work no R-ID asks for goes into a separate issue, not this PR. A contradiction between `plan.md` and the code stops the work: ask the owner.
