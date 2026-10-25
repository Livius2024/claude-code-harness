#!/usr/bin/env python3
"""Fail a pull request that touches owner-only paths until the owner labels it.

The owner approves every change to domain rules (tax, audit, accounting, legal),
to the gates themselves and to the agent rules. Those paths are listed, one
glob per line, in `.github/owner-approval-paths.txt`. When a pull request
changes any of them, this check fails until the PR carries the
`owner-approved` label, which only the owner adds. The check runs again when a
label is added or removed, so adding the label turns it green and lets
auto-merge proceed.

Usage (from CI): check_owner_approval.py --base <sha> --head <sha> --labels "a,b"
Standard library only.
"""

from __future__ import annotations

import argparse
import fnmatch
import subprocess
import sys
from pathlib import Path

LABEL = "owner-approved"
PATTERNS_FILE = Path(".github/owner-approval-paths.txt")


def read_patterns(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def matches(path: str, pattern: str) -> bool:
    # `dir/**` covers everything below dir; `**/x` also matches x at the root.
    if pattern.endswith("/**") and path.startswith(pattern[:-2]):
        return True
    if pattern.startswith("**/") and fnmatch.fnmatchcase(path, pattern[3:]):
        return True
    return fnmatch.fnmatchcase(path, pattern)


def protected_changes(changed: list[str], patterns: list[str]) -> list[str]:
    return [path for path in changed if any(matches(path, p) for p in patterns)]


def changed_files(base: str, head: str) -> list[str]:
    out = subprocess.run(
        # --no-renames: a rename must list its protected source path too, or
        # moving spec.md to other.md would slip past the gate.
        ["git", "diff", "--name-only", "--no-renames", f"{base}...{head}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Require the owner-approved label for owner-only paths.")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--labels", default="", help="comma-separated PR labels")
    parser.add_argument("--patterns", type=Path, default=PATTERNS_FILE)
    args = parser.parse_args(argv)

    hits = protected_changes(changed_files(args.base, args.head), read_patterns(args.patterns))
    if not hits:
        print("check_owner_approval: no owner-only paths changed")
        return 0
    labels = {label.strip() for label in args.labels.split(",") if label.strip()}
    print("check_owner_approval: this PR changes owner-only paths:")
    for path in hits:
        print(f"  {path}")
    if LABEL in labels:
        print(f"check_owner_approval: `{LABEL}` label present, approved")
        return 0
    print(f"::error::Owner approval needed: add the `{LABEL}` label after reviewing the files above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
