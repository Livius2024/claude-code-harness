# Definition of done (every session, cloud and local)

This file has no `paths:` on purpose: cloud threads load it too.

Work is **done** only when `python scripts/check_done.py` exits 0 on the final tree. It runs four checks for every stack in the project: **Tests, Lint, Typecheck, Build** (from `.claude/done.json`, or detected: Python = pytest, ruff, pyright or mypy, build or compileall; TypeScript = the package scripts or `tsc --noEmit`; Go = `go test`, `golangci-lint`, `go vet`, `go build`; .NET = `dotnet test`, `dotnet format`, `dotnet build`).

## Before you say done

- Run `python scripts/check_done.py` after your last change and read its output. Words like "done", "gata", "finished", "ready to merge", "works", or a PR marked ready are claims of done: make none of them unless the run exited 0.
- Put its table (the status lines and the verdict) in your report and in the PR body, with the commit SHA it ran on.
- **Exit 1 (FAIL):** fix the code and run it again. After 3 failed repair attempts the work is **BLOCAT**: report the failing check and your diagnosis.
- **Exit 2 (NEVERIFICAT):** a check did not run (missing tool, wrong OS, timeout, no tests). Install the tool if you can and run it again. Otherwise report the work as **not done, NEVERIFICAT**, naming each check that did not run and why. Never write PASS for it.
- A check you ran by hand instead of through the script still counts only if you show its command and output.

## Never

- Never edit `.claude/done.json`, `scripts/check_done.py` or the CI to drop, skip, mark `not_applicable`/`covered_by` or loosen a check so the run turns green. These files are owner-approval paths.
- Never skip, delete or weaken a test or a lint rule to get exit 0 (`.claude/rules/factory.md` → Never).

## Where the same gate runs

| Where | How |
|---|---|
| Cloud threads (no hooks there) | This rule: you run the script yourself before reporting. |
| Locally (Claude Code CLI / desktop) | The global Stop hook (`verify-gate`) runs `.claude/verify.json`, which calls this script, and keeps you working while it fails. |
| GitHub | The CI `checks` job runs the same script; a PR merges only on green. |
