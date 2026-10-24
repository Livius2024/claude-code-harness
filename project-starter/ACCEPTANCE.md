# ACCEPTANCE.md — <project name>

One row per requirement from `spec.md`. The checker (Codex when Claude Code built, Claude when Codex built, and the owner) reads this file, not the builder's summary.

Rules:
- Status is one of **PASS**, **FAIL**, **NEVERIFICAT** (the check did not run: timeout, missing tool, missing access), **BLOCAT** (repair budget spent; diagnosis in Evidence).
- A row without a command or scenario can never be PASS.
- Status changes only with the real result of the command on the SHA in the row. A new commit resets affected rows to NEVERIFICAT until re-run.
- Evidence is a path: test output, screenshot under `.scratch/evidence/<id>/`, or a log. Nobody relaxes a criterion to make a row green.

| ID | Requirement (owner's words) | Verifiable criterion | Command or browser scenario | Status | SHA | Evidence |
|---|---|---|---|---|---|---|
| R1 | <e.g. Import a CSV of invoices> | <Rows appear in the list with totals matching the file to the cent> | <`npm test -- import` / open /import, upload `fixtures/invoices.csv`, compare totals> | NEVERIFICAT | | |
| R2 | <...> | <...> | <...> | NEVERIFICAT | | |
