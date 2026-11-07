#!/usr/bin/env python3
"""Definition of done: tests, lint, type check and build must all pass.

One command decides whether work may be called done, in every place it runs:
an agent before it reports, Claude Code's Stop hook (through `.claude/verify.json`)
and the CI `checks` job.

    python scripts/check_done.py            # run the checks
    python scripts/check_done.py --list     # show the plan, run nothing

The checks come from `.claude/done.json` when it exists, otherwise from the
stacks found in the project root (pyproject.toml, package.json, go.mod, *.sln).

Exit codes: 0 every check passed; 1 a check failed or the setup is wrong;
2 nothing failed but a check did not run (NEVERIFICAT). Only 0 means done.

Standard library only: projects run it without installing anything.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

NAMES = ("Tests", "Lint", "Typecheck", "Build")
CONFIG = Path(".claude/done.json")
DEFAULT_TIMEOUT = 600
TAIL_LINES = 40

PASS, FAIL, NEVER, NA = "PASS", "FAIL", "NEVERIFICAT", "N/A"


@dataclass
class Check:
    name: str
    stack: str
    run: list[str] = field(default_factory=list)
    os: str | None = None
    covered_by: str | None = None
    why: str = ""
    not_applicable: str | None = None


@dataclass
class Result:
    check: Check
    status: str
    detail: str = ""
    tail: str = ""


class SetupError(Exception):
    pass


# --- plan: from .claude/done.json or from the stacks found -------------------


def quote(arg: str) -> str:
    """Quote for the shell that runs the commands: cmd.exe on Windows, sh elsewhere."""
    return f'"{arg}"' if os.name == "nt" else shlex.quote(arg)


def load_config(path: Path) -> tuple[list[Check], int, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SetupError(f"{path}: cannot read it as JSON ({exc})") from exc
    if not isinstance(data, dict) or not isinstance(data.get("checks"), list):
        raise SetupError(f'{path}: expected an object with a "checks" list')
    checks: list[Check] = []
    for i, raw in enumerate(data["checks"], 1):
        where = f"{path}: check {i}"
        if not isinstance(raw, dict):
            raise SetupError(f"{where}: expected an object")
        name = raw.get("name")
        if name not in NAMES:
            raise SetupError(f"{where}: name must be one of {', '.join(NAMES)}")
        run = raw.get("run", [])
        if isinstance(run, str):
            run = [run]
        modes = [bool(run), "covered_by" in raw, "not_applicable" in raw]
        if sum(modes) != 1:
            raise SetupError(f'{where}: give exactly one of "run", "covered_by" or "not_applicable"')
        if not all(isinstance(c, str) and c.strip() for c in run):
            raise SetupError(f'{where}: "run" must hold non-empty command strings')
        if "covered_by" in raw and not str(raw.get("why", "")).strip():
            raise SetupError(f'{where}: "covered_by" needs a "why"')
        if "not_applicable" in raw and not str(raw["not_applicable"]).strip():
            raise SetupError(f'{where}: "not_applicable" needs the reason')
        checks.append(
            Check(
                name=name,
                stack=str(raw.get("stack", "project")),
                run=list(run),
                os=raw.get("os"),
                covered_by=raw.get("covered_by"),
                why=str(raw.get("why", "")),
                not_applicable=raw.get("not_applicable"),
            )
        )
    timeout = data.get("timeoutSec", DEFAULT_TIMEOUT)
    unset_env = data.get("unsetEnv", [])
    if not isinstance(timeout, int) or timeout <= 0:
        raise SetupError(f'{path}: "timeoutSec" must be a positive whole number')
    if not isinstance(unset_env, list) or not all(isinstance(p, str) for p in unset_env):
        raise SetupError(f'{path}: "unsetEnv" must be a list of names or NAME_* patterns')
    validate(checks, str(path))
    return checks, timeout, unset_env


def validate(checks: list[Check], source: str) -> None:
    missing = [n for n in NAMES if not any(c.name == n for c in checks)]
    if missing:
        raise SetupError(f"{source}: no {', '.join(missing)} check; the definition of done needs all four")
    for c in checks:
        if c.covered_by and not any(o.stack == c.stack and o.name == c.covered_by and o.run for o in checks):
            raise SetupError(f"{source}: {c.stack} {c.name} is covered by {c.covered_by}, which has no command")


def python_checks(root: Path, temp: Path) -> list[Check]:
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    try:
        pyproject = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise SetupError(f"pyproject.toml: {exc}") from exc
    uv = shutil.which("uv") is not None
    py = "python" if os.name == "nt" else "python3"

    def tool(module: str, listed: bool) -> str:
        if not uv:
            return f"{py} -m {module}"
        return f"uv run {module}" if listed else f"uv run --with {module} {module}"

    deps = text.lower()
    ruff = "uvx ruff" if uv and "ruff" not in deps else tool("ruff", True)
    tool_cfg = pyproject.get("tool", {})
    if "mypy" in tool_cfg:
        typecheck = f"{tool('mypy', 'mypy' in deps)} ."
    else:
        typecheck = tool("pyright", "pyright" in deps)
    if "build-system" in pyproject:
        out = quote(str(temp / "dist"))
        build = f"uv build --out-dir {out}" if uv else f"{py} -m build --outdir {out}"
    else:
        skip = r"(^|[/\\])(\.venv|venv|\.git|node_modules|build|dist)([/\\]|$)"
        build = f"{'uv run python' if uv else py} -m compileall -q -x {quote(skip)} ."
    return [
        Check("Tests", "Python", [f"{tool('pytest', True)} -q"]),
        Check("Lint", "Python", [f"{ruff} check .", f"{ruff} format --check ."]),
        Check("Typecheck", "Python", [typecheck]),
        Check("Build", "Python", [build]),
    ]


def node_checks(root: Path) -> list[Check]:
    try:
        scripts = json.loads((root / "package.json").read_text(encoding="utf-8")).get("scripts", {}) or {}
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        raise SetupError(f"package.json: {exc}") from exc
    pm = "pnpm" if (root / "pnpm-lock.yaml").exists() else "yarn" if (root / "yarn.lock").exists() else "npm"
    execute = {"pnpm": "pnpm exec", "yarn": "yarn", "npm": "npx"}[pm]

    def script(*names: str) -> list[str]:
        found = next((s for s in names if s in scripts), names[0])
        return [f"{pm} run {found}"]  # a missing script fails the check, which is the point

    typecheck = Check("Typecheck", "Node", script("typecheck", "type-check", "tsc"))
    if not any(s in scripts for s in ("typecheck", "type-check", "tsc")):
        if (root / "tsconfig.json").exists():
            typecheck = Check("Typecheck", "Node", [f"{execute} tsc --noEmit"])
        else:
            typecheck = Check("Typecheck", "Node", not_applicable="no tsconfig.json: plain JavaScript")
    return [
        Check("Tests", "Node", script("test")),
        Check("Lint", "Node", script("lint")),
        typecheck,
        Check("Build", "Node", script("build")),
    ]


def go_checks() -> list[Check]:
    return [
        Check("Tests", "Go", ["go test ./..."]),
        Check("Lint", "Go", ["golangci-lint run"]),
        Check("Typecheck", "Go", ["go vet ./..."]),
        Check("Build", "Go", ["go build ./..."]),
    ]


def dotnet_checks(target: str) -> list[Check]:
    t = quote(target)
    return [
        Check("Tests", ".NET", [f"dotnet test {t} -c Release"]),
        Check("Lint", ".NET", [f"dotnet format {t} --verify-no-changes"]),
        Check("Typecheck", ".NET", covered_by="Build", why="the C# compiler checks types while it builds"),
        Check("Build", ".NET", [f"dotnet build {t} -c Release"]),
    ]


def dotnet_target(root: Path) -> str | None:
    for pattern in ("*.sln", "*.slnx", "*.csproj", "*/*.sln", "*/*.slnx"):
        found = sorted(root.glob(pattern))
        if found:
            return found[0].relative_to(root).as_posix()
    return None


def detect(root: Path, temp: Path) -> list[Check]:
    checks: list[Check] = []
    if (root / "pyproject.toml").exists():
        checks += python_checks(root, temp)
    if (root / "package.json").exists():
        checks += node_checks(root)
    if (root / "go.mod").exists():
        checks += go_checks()
    target = dotnet_target(root)
    if target:
        checks += dotnet_checks(target)
    return checks


# --- run ----------------------------------------------------------------------


def run_command(command: str, root: Path, timeout: int, env: dict[str, str]) -> tuple[int | None, str]:
    """Return (exit code, output); exit code None means the command timed out."""
    # Its own process group, so a timeout stops the whole tree, not only the shell.
    proc = subprocess.Popen(
        command,
        shell=True,
        cwd=root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=os.name != "nt",
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
    )
    try:
        out, _ = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        out, _ = proc.communicate()
        return None, out.decode("utf-8", errors="replace")
    return proc.returncode, out.decode("utf-8", errors="replace")


def kill_tree(proc: subprocess.Popen) -> None:
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], check=False, capture_output=True)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def missing_tool(command: str) -> str | None:
    try:
        first = shlex.split(command, posix=os.name != "nt")[0]
    except (ValueError, IndexError):
        return None
    if "=" in first or first in {"cd", "set", "export"}:
        return None
    return None if shutil.which(first) else first


MISSING_MODULE = re.compile(r"No module named ['\"]?([\w.]+)")


def run_check(check: Check, root: Path, timeout: int, env: dict[str, str]) -> Result:
    if check.not_applicable:
        return Result(check, NA, check.not_applicable)
    if check.os and not sys.platform.startswith(check.os.lower().replace("windows", "win32")):
        return Result(check, NEVER, f"needs {check.os}; this machine is {sys.platform}")
    for command in check.run:
        tool = missing_tool(command)
        if tool:
            return Result(check, NEVER, f"`{tool}` is not installed here")
        started = time.monotonic()
        code, out = run_command(command, root, timeout, env)
        seconds = time.monotonic() - started
        tail = "\n".join(out.rstrip().splitlines()[-TAIL_LINES:])
        if code is None:
            return Result(check, NEVER, f"`{command}` timed out after {timeout}s", tail)
        if code == 5 and "pytest" in command:
            return Result(check, NEVER, f"`{command}` collected no tests", tail)
        module = MISSING_MODULE.search(out)
        if code != 0 and module and f"-m {module.group(1).split('.')[0]}" in command:
            return Result(check, NEVER, f"Python module `{module.group(1)}` is not installed", tail)
        if code != 0:
            return Result(check, FAIL, f"`{command}` exited {code} after {seconds:.0f}s", tail)
    return Result(check, PASS)


def clean_env(patterns: list[str]) -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if not any(fnmatchcase(k.upper(), p.upper()) for p in patterns)}


def verdict(results: list[Result]) -> int:
    statuses = {r.status for r in results}
    if FAIL in statuses:
        return 1
    if NEVER in statuses:
        return 2
    return 0


def describe(check: Check) -> str:
    if check.not_applicable:
        return "(not applicable)"
    if check.covered_by:
        return f"(in {check.covered_by}: {check.why})"
    return " && ".join(check.run)


def report(results: list[Result], root: Path) -> int:
    print(f"Definition of done — {root}")
    for r in results:
        print(f"  {r.status:<11}  {r.check.stack:<7} {r.check.name:<9}  {describe(r.check)}")
        if r.detail and r.status != PASS:
            print(f"{'':16}{r.detail}")
    for r in results:
        if r.status in (FAIL, NEVER) and r.tail:
            print(f"\n--- {r.check.stack} {r.check.name}: last lines ---\n{r.tail}")
    code = verdict(results)
    failed = sum(r.status == FAIL for r in results)
    never = sum(r.status == NEVER for r in results)
    print()
    if code == 0:
        print("DONE: every check passed.")
    elif code == 1:
        print(f"NOT DONE: {failed} check(s) failed. Fix the code; never report this work as done.")
    else:
        print(f"NOT DONE: {never} check(s) did not run (NEVERIFICAT). Report them as NEVERIFICAT, never as passed.")
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the definition of done: tests, lint, type check, build.")
    parser.add_argument("--root", type=Path, default=Path("."), help="project folder (default: current)")
    parser.add_argument("--list", action="store_true", help="print the checks without running them")
    parser.add_argument(
        "--allow-empty", action="store_true", help="exit 0 when no stack is found (a starter repo with no code yet)"
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
    root = args.root.resolve()
    with tempfile.TemporaryDirectory(prefix="check_done_") as temp:
        try:
            config = root / CONFIG
            if config.exists():
                checks, timeout, unset_env = load_config(config)
            else:
                checks, timeout, unset_env = detect(root, Path(temp)), DEFAULT_TIMEOUT, []
                if checks:
                    validate(checks, "detected stacks")
        except SetupError as exc:
            print(f"check_done: {exc}")
            return 1
        if not checks:
            print(f"check_done: no stack found in {root} and no {CONFIG.as_posix()}.")
            if args.allow_empty:
                print("Nothing to verify yet (--allow-empty).")
                return 0
            print("NOT DONE: nothing was verified (NEVERIFICAT). Add the project's commands to .claude/done.json.")
            return 2
        if args.list:
            for c in checks:
                print(f"{c.stack:<7} {c.name:<9}  {describe(c)}" + (f"  [{c.os} only]" if c.os else ""))
            return 0
        env = clean_env(unset_env)
        results = [run_check(c, root, timeout, env) for c in checks]
        by_key = {(r.check.stack, r.check.name): r for r in results if r.check.run}
        for r in results:
            if r.check.covered_by:
                source = by_key[(r.check.stack, r.check.covered_by)]
                r.status, r.detail = source.status, source.detail
        return report(results, root)


if __name__ == "__main__":
    sys.exit(main())
