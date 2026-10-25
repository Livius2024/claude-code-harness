#!/usr/bin/env python3
"""Fail when a browser check can run without the backend guard.

e2e/fixtures.ts wraps Playwright's `test` so every check also fails on a
failed request to the app (HTTP 4xx/5xx, connection error) and on an error in
the server log. A spec that gets `test` from Playwright another way skips that
guard, so this script fails when any file under e2e/ other than fixtures.ts
and the playwright.config.* files imports a value from a Playwright package (directly,
or in a helper the spec imports; type-only imports are fine), or when
e2e/fixtures.ts is missing. CI runs it before the browser checks; the
`backend-guard` annotation checked by browser_qa_comment.py --require-guard
proves at run time that every check went through the guard.
Standard library only, so it runs in any project without installing anything.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SUFFIXES = {".ts", ".js", ".mts", ".mjs", ".cts", ".cjs", ".tsx", ".jsx"}
# `import { test } from '@playwright/test'`, `export ... from`, `require(...)`, `import(...)`.
VALUE_IMPORT = re.compile(
    r"""(?:^|[;\s])(?:import(?!\s+type\b)[^;]*?\bfrom|export(?!\s+type\b)[^;]*?\bfrom|require\s*\(|import\s*\()"""
    r"""\s*['"][^'"]*playwright[^'"]*['"]""",
    re.MULTILINE,
)


# Installed packages and Playwright's own output, not the project's code.
SKIP_DIRS = {"node_modules", "test-results", "report", "playwright-report"}


# The guard itself, the app's config and the guard self-test's config (e2e/guard-selftest/).
CONFIG_DIRS = {(), ("guard-selftest",)}


def allowed(path: Path, e2e: Path) -> bool:
    rel = path.relative_to(e2e)
    return rel.as_posix() == "fixtures.ts" or (
        rel.parts[:-1] in CONFIG_DIRS and rel.name.startswith("playwright.config.")
    )


def offenders(e2e: Path) -> list[Path]:
    found = []
    for path in sorted(e2e.rglob("*")):
        if SKIP_DIRS.intersection(path.relative_to(e2e).parts[:-1]) or path.suffix not in SUFFIXES:
            continue
        if path.is_file() and not allowed(path, e2e) and VALUE_IMPORT.search(path.read_text(encoding="utf-8")):
            found.append(path)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that every browser check uses e2e/fixtures.ts.")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    e2e = args.root / "e2e"
    problems = []
    if not (e2e / "fixtures.ts").is_file():
        problems.append("e2e/fixtures.ts is missing: it holds the backend guard every check needs.")
    for path in offenders(e2e) if e2e.is_dir() else []:
        rel = path.relative_to(args.root).as_posix()
        problems.append(f"{rel} imports from Playwright; import {{ test, expect }} from e2e/fixtures.ts.")
    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        return 1
    print("Every browser check uses the backend guard (e2e/fixtures.ts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
