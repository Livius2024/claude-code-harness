#!/usr/bin/env python3
"""Fail CI when the requirements manifest and ACCEPTANCE.md disagree.

The manifest is the `## Requirements` section of spec.md: one list item per
requirement, numbered R1, R2, ... (`- R1: Import a CSV of invoices`).
ACCEPTANCE.md must hold exactly one table row per manifest ID.

Checks:
- every manifest ID has an ACCEPTANCE row, and no row exists for an unknown ID;
- no ID is duplicated in either file;
- Status is PASS, FAIL, NEVERIFICAT or BLOCAT;
- a PASS row has a real command or scenario, a SHA and an evidence path.

Before spec.md exists (a fresh starter) there is nothing to check and it exits 0.
Standard library only, so it runs in any project without installing anything.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

STATUSES = {"PASS", "FAIL", "NEVERIFICAT", "BLOCAT"}
ID_RE = re.compile(r"^R\d+$")
MANIFEST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\**(R\d+)\**\s*[:.)\-–—]")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
HEADER = ("id", "requirement", "criterion", "command", "status", "sha", "evidence")


@dataclass
class Row:
    line: int
    cells: dict[str, str]


def read_manifest(spec: Path) -> tuple[list[str], list[str]]:
    """Return the requirement IDs under `## Requirements` and any errors."""
    ids: list[str] = []
    errors: list[str] = []
    in_section = False
    for number, raw in enumerate(spec.read_text(encoding="utf-8").splitlines(), 1):
        if raw.startswith("## "):
            in_section = raw[3:].strip().lower().startswith("requirements")
            continue
        if not in_section:
            continue
        match = MANIFEST_ITEM_RE.match(raw)
        if match:
            rid = match.group(1)
            if rid in ids:
                errors.append(f"spec.md:{number}: {rid} is listed twice in ## Requirements")
            else:
                ids.append(rid)
    return ids, errors


def is_placeholder(cell: str) -> bool:
    text = cell.strip().strip("`").strip()
    return not text or (text.startswith("<") and text.endswith(">"))


def split_row(raw: str) -> list[str]:
    return [cell.strip() for cell in raw.strip().strip("|").split("|")]


def read_acceptance(path: Path) -> tuple[list[Row], list[str]]:
    """Return the rows of the first table whose first column is `ID`."""
    rows: list[Row] = []
    errors: list[str] = []
    in_table = False
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.lstrip().startswith("|"):
            if in_table:
                break
            continue
        cells = split_row(raw)
        if not in_table:
            if cells and cells[0].lower() == "id":
                if len(cells) != len(HEADER):
                    errors.append(
                        f"ACCEPTANCE.md:{number}: table needs {len(HEADER)} columns "
                        "(ID, Requirement, Criterion, Command or scenario, Status, SHA, Evidence)"
                    )
                    return rows, errors
                in_table = True
            continue
        if all(set(c) <= set(":- ") for c in cells):
            continue  # the |---|---| separator
        if len(cells) != len(HEADER):
            errors.append(f"ACCEPTANCE.md:{number}: row has {len(cells)} columns, expected {len(HEADER)}")
            continue
        rows.append(Row(number, dict(zip(HEADER, cells, strict=True))))
    if not in_table:
        errors.append("ACCEPTANCE.md: no table with an `ID` column found")
    return rows, errors


def check(root: Path) -> tuple[list[str], list[str]]:
    """Return (errors, notes) for the project at `root`."""
    spec = root / "spec.md"
    acceptance = root / "ACCEPTANCE.md"
    if not spec.exists():
        return [], ["spec.md does not exist yet; nothing to check."]
    if not acceptance.exists():
        return ["ACCEPTANCE.md is missing but spec.md exists"], []

    manifest, errors = read_manifest(spec)
    if not manifest:
        errors.append("spec.md has no requirements: add `## Requirements` with items like `- R1: ...`")
    rows, row_errors = read_acceptance(acceptance)
    errors += row_errors

    seen: dict[str, int] = {}
    for row in rows:
        rid = row.cells["id"].strip("*` ")
        where = f"ACCEPTANCE.md:{row.line}"
        if is_placeholder(rid):
            errors.append(f"{where}: placeholder row left in the table; replace it or delete it")
            continue
        if not ID_RE.match(rid):
            errors.append(f"{where}: ID `{rid}` is not of the form R<number>")
            continue
        if rid in seen:
            errors.append(f"{where}: {rid} already has a row at line {seen[rid]}")
            continue
        seen[rid] = row.line
        if rid not in manifest:
            errors.append(f"{where}: {rid} is not in spec.md ## Requirements")

        status = row.cells["status"].strip("*` ").upper()
        if status not in STATUSES:
            errors.append(f"{where}: {rid} status `{row.cells['status']}` is not one of {sorted(STATUSES)}")
        if is_placeholder(row.cells["criterion"]):
            errors.append(f"{where}: {rid} has no verifiable criterion")
        if status == "PASS":
            if is_placeholder(row.cells["command"]):
                errors.append(f"{where}: {rid} is PASS without a command or scenario")
            if not SHA_RE.match(row.cells["sha"].strip("` ")):
                errors.append(f"{where}: {rid} is PASS without the SHA it was checked on")
            if is_placeholder(row.cells["evidence"]):
                errors.append(f"{where}: {rid} is PASS without an evidence path")

    for rid in manifest:
        if rid not in seen:
            errors.append(f"{rid} is in spec.md but has no ACCEPTANCE.md row")

    notes = [f"{len(manifest)} requirements, {len(seen)} acceptance rows"]
    return errors, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check spec.md requirements against ACCEPTANCE.md.")
    parser.add_argument("--root", type=Path, default=Path("."), help="project folder (default: current)")
    args = parser.parse_args(argv)

    errors, notes = check(args.root)
    for note in notes:
        print(f"check_acceptance: {note}")
    for error in errors:
        print(f"::error::{error}" if _in_github_actions() else f"ERROR: {error}")
    return 1 if errors else 0


def _in_github_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


if __name__ == "__main__":
    sys.exit(main())
