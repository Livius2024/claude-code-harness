#!/usr/bin/env python3
"""Turn a Playwright JSON report into the browser QA comment for a PR.

Reads e2e/results.json (Playwright's `json` reporter), copies every screenshot
attachment to <out>/shots/ under a short unique name, and writes
<out>/comment.md: a summary line, one row per check with its status at each
size (desktop, phone), then the screenshots. A check titled with an R-ID
("R3 shows the VAT total", also inside a describe block) is labelled with it, so the comment maps to
ACCEPTANCE.md.

When the report is missing (the app did not start, Playwright crashed) the
comment says NEVERIFICAT instead of pretending the checks passed, and so does
a skipped check: only checks that ran and passed at every size are green.
With --strict the script exits 1 unless the result is green, which is what
fails the `browser-qa` job.

--image-base is the URL the shots will be published under (CI pushes them to
a branch); without it the comment links them relative to <out>, for local use.
Standard library only, so it runs in any project without installing anything.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

MARKER = "<!-- browser-qa -->"
R_ID_RE = re.compile(r"\b(R\d+)\b")
STATUS = {
    "expected": "✅ PASS",
    "unexpected": "❌ FAIL",
    "flaky": "⚠️ FLAKY",
    "skipped": "⏭️ NEVERIFICAT (skipped)",
}
ERROR_CHARS = 600


@dataclass
class Shot:
    name: str
    source: Path | None = None
    body: bytes | None = None


@dataclass
class Run:
    project: str
    status: str
    error: str = ""
    shots: list[Shot] = field(default_factory=list)


@dataclass
class Check:
    title: str
    file: str
    runs: list[Run] = field(default_factory=list)

    @property
    def requirement(self) -> str:
        match = R_ID_RE.search(self.title)
        return match.group(1) if match else ("smoke" if self.title.lower().startswith("smoke") else "")

    @property
    def status(self) -> str:
        statuses = {run.status for run in self.runs}
        # A size that was skipped makes the check unverified, even if another passed.
        for worst in ("unexpected", "flaky", "skipped"):
            if worst in statuses:
                return worst
        return "expected" if statuses else "skipped"


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "check"


def _specs(suite: dict, titles: list[str], *, top: bool = True):
    """Yield (full title, file, spec) for every spec in a suite tree.

    Top-level suites are files; nested ones are `test.describe` blocks, whose
    titles prefix the check's title.
    """
    here = titles if top else [*titles, suite.get("title", "")]
    for spec in suite.get("specs", []):
        yield " › ".join([*here, spec["title"]]), spec.get("file", suite.get("file", "")), spec
    for child in suite.get("suites", []):
        yield from _specs(child, here, top=False)


def _first_error(result: dict) -> str:
    errors = result.get("errors") or ([result["error"]] if result.get("error") else [])
    if not errors:
        return ""
    text = re.sub(r"\x1b\[[0-9;]*m", "", errors[0].get("message", "")).strip()
    return text[:ERROR_CHARS] + ("…" if len(text) > ERROR_CHARS else "")


def read_checks(report: dict) -> list[Check]:
    # With fullyParallel the report repeats a spec once per project; merge them.
    checks: dict[tuple[str, str], Check] = {}
    for suite in report.get("suites", []):
        for title, file, spec in _specs(suite, []):
            check = checks.setdefault((file, title), Check(title=title, file=file))
            for test in spec.get("tests", []):
                results = test.get("results") or [{}]
                last = results[-1]
                run = Run(project=test.get("projectName", ""), status=test.get("status", "skipped"))
                if run.status in ("unexpected", "flaky"):
                    run.error = _first_error(last)
                for attachment in last.get("attachments", []):
                    if not attachment.get("contentType", "").startswith("image/"):
                        continue
                    if attachment.get("path"):
                        run.shots.append(Shot(attachment.get("name", "screenshot"), source=Path(attachment["path"])))
                    elif attachment.get("body"):
                        body = base64.b64decode(attachment["body"])
                        run.shots.append(Shot(attachment.get("name", "screenshot"), body=body))
                check.runs.append(run)
    return list(checks.values())


def copy_shots(checks: list[Check], shots_dir: Path) -> dict[int, str]:
    """Copy every screenshot to shots_dir; return id(shot) -> file name."""
    names: dict[int, str] = {}
    shots_dir.mkdir(parents=True, exist_ok=True)
    for index, check in enumerate(checks, start=1):
        for run in check.runs:
            for number, shot in enumerate(run.shots, start=1):
                name = f"{index:02d}-{slug(check.title)}-{slug(run.project)}-{number}.png"
                target = shots_dir / name
                if shot.source is not None and shot.source.is_file():
                    shutil.copyfile(shot.source, target)
                elif shot.body is not None:
                    target.write_bytes(shot.body)
                else:
                    continue
                names[id(shot)] = name
    return names


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def _url(base: str, name: str) -> str:
    return f"{base.rstrip('/')}/{name}?raw=true" if base else f"shots/{name}"


def is_green(checks: list[Check]) -> bool:
    return bool(checks) and all(check.status == "expected" for check in checks)


def headline(checks: list[Check]) -> str:
    if is_green(checks):
        return "✅ Browser QA"
    if checks and all(check.status in ("expected", "skipped") for check in checks):
        return "⚠️ Browser QA: NEVERIFICAT"
    return "❌ Browser QA"


def render(checks: list[Check], names: dict[int, str], *, image_base: str, run_url: str, sha: str) -> str:
    projects = list(dict.fromkeys(run.project for check in checks for run in check.runs))
    counts = {key: sum(1 for check in checks if check.status == key) for key in STATUS}
    summary = " · ".join(f"{STATUS[key]} {counts[key]}" for key in STATUS if counts[key])

    lines = [MARKER, f"## {headline(checks)}", ""]
    meta = [f"Commit `{sha[:7]}`" if sha else "", f"[run, full report and traces]({run_url})" if run_url else ""]
    lines += [f"{summary or 'No checks found in e2e/tests/'}", " · ".join(part for part in meta if part), ""]

    if checks:
        lines.append("| Check | Requirement | " + " | ".join(projects) + " |")
        lines.append("|---|---|" + "---|" * len(projects))
        for check in checks:
            by_project = {run.project: STATUS.get(run.status, run.status) for run in check.runs}
            cells = [by_project.get(project, "—") for project in projects]
            lines.append(f"| {_cell(check.title)} | {check.requirement or '—'} | " + " | ".join(cells) + " |")
        lines.append("")

    for check in checks:
        lines += [f"### {STATUS[check.status].split()[0]} {_cell(check.title)}", ""]
        for run in check.runs:
            if run.error:
                fence = "````" if "```" in run.error else "```"
                lines += [f"**{run.project}:**", fence, run.error, fence, ""]
        shot_runs = [run for run in check.runs if any(id(shot) in names for shot in run.shots)]
        if shot_runs:
            lines.append("| " + " | ".join(run.project for run in shot_runs) + " |")
            lines.append("|" + "---|" * len(shot_runs))
            cells = []
            for run in shot_runs:
                width = 220 if run.project == "phone" else 440
                images = [
                    f'<img src="{_url(image_base, names[id(shot)])}" width="{width}" alt="{_cell(check.title)}">'
                    for shot in run.shots
                    if id(shot) in names
                ]
                cells.append(" ".join(images))
            lines += ["| " + " | ".join(cells) + " |", ""]
    return "\n".join(lines).rstrip() + "\n"


def render_not_run(reason: str, *, run_url: str, sha: str) -> str:
    meta = [f"Commit `{sha[:7]}`" if sha else "", f"[run log]({run_url})" if run_url else ""]
    lines = [MARKER, "## ⚠️ Browser QA: NEVERIFICAT", "", f"The browser checks did not produce a report: {reason}"]
    lines += ["", " · ".join(part for part in meta if part)]
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the browser QA PR comment from a Playwright JSON report.")
    parser.add_argument("--results", type=Path, default=Path("e2e/results.json"))
    parser.add_argument("--out", type=Path, default=Path("qa-out"))
    parser.add_argument("--image-base", default="", help="URL the shots are published under")
    parser.add_argument("--run-url", default="")
    parser.add_argument("--sha", default="")
    parser.add_argument("--strict", action="store_true", help="exit 1 unless every check ran and passed")
    args = parser.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)
    green = False
    try:
        report = json.loads(args.results.read_text(encoding="utf-8"))
    except FileNotFoundError:
        comment = render_not_run(
            f"`{args.results}` is missing (did the app start?).", run_url=args.run_url, sha=args.sha
        )
    except json.JSONDecodeError as exc:
        comment = render_not_run(f"`{args.results}` is not valid JSON ({exc}).", run_url=args.run_url, sha=args.sha)
    else:
        checks = read_checks(report)
        names = copy_shots(checks, args.out / "shots")
        comment = render(checks, names, image_base=args.image_base, run_url=args.run_url, sha=args.sha)
        green = is_green(checks)
    (args.out / "comment.md").write_text(comment, encoding="utf-8")
    print(comment)
    return 1 if args.strict and not green else 0


if __name__ == "__main__":
    sys.exit(main())
