#!/usr/bin/env python3
"""Fail when a browser check can run without the backend guard.

e2e/fixtures.ts wraps Playwright's `test` so every check also fails on a
failed request to the app (HTTP 4xx/5xx, connection error) and on an error in
the server log. A spec that imports `test` straight from '@playwright/test'
skips that guard, so this script fails when any file under e2e/tests/ imports
a value from '@playwright/test' (type-only imports are fine), or when
e2e/fixtures.ts is missing. CI runs it before the browser checks.
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
    r"""(?:^|[;\s])(?:import(?!\s+type\b)[^;]*?\bfrom|export[^;]*?\bfrom|require\s*\(|import\s*\()\s*['"]@playwright/test['"]""",
    re.MULTILINE,
)


def offenders(tests_dir: Path) -> list[Path]:
    found = []
    for path in sorted(tests_dir.rglob("*")):
        if path.suffix in SUFFIXES and path.is_file() and VALUE_IMPORT.search(path.read_text(encoding="utf-8")):
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
    for path in offenders(e2e / "tests"):
        rel = path.relative_to(args.root).as_posix()
        problems.append(f"{rel} imports from '@playwright/test'; import {{ test, expect }} from e2e/fixtures.ts.")
    if problems:
        for problem in problems:
            print(f"::error::{problem}")
        return 1
    print("Every browser check uses the backend guard (e2e/fixtures.ts).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
