# ACCEPTANCE.md — <project name>

Exactly one row per requirement in the manifest: the `## Requirements` section of `spec.md`, written as

```
## Requirements

- R1: Import a CSV of invoices
- R2: Show the VAT total per month
```

CI (`python scripts/check_acceptance.py`) fails when a manifest ID has no row, a row has an ID not in the manifest, an ID repeats, a status is not one of the four below, or a PASS row lacks its command, SHA or evidence. Until `spec.md` exists the check passes; delete the `<...>` example rows when you add the first real ones. The checker (Codex when Claude Code built, Claude when Codex built, and the owner) reads this file, not the builder's summary.

Rules:
- Status is one of **PASS**, **FAIL**, **NEVERIFICAT** (the check did not run: timeout, missing tool, missing access), **BLOCAT** (repair budget spent; diagnosis in Evidence).
- A row without a command or scenario can never be PASS.
- Status changes only with the real result of the command on the SHA in the row. A new commit resets affected rows to NEVERIFICAT until re-run.
- Evidence is a path: test output, screenshot under `.scratch/evidence/<id>/`, or a log. Nobody relaxes a criterion to make a row green.

| ID | Requirement (owner's words) | Verifiable criterion | Command or browser scenario | Status | SHA | Evidence |
|---|---|---|---|---|---|---|
| R1 | <e.g. Import a CSV of invoices> | <Rows appear in the list with totals matching the file to the cent> | <`npm test -- import` / open /import, upload `fixtures/invoices.csv`, compare totals> | NEVERIFICAT | | |
| R2 | <...> | <...> | <...> | NEVERIFICAT | | |
