import json
import os
import subprocess
from pathlib import Path

import pytest
from conftest import STARTER

SCRIPT = STARTER / "scripts" / "browser_qa_publish.sh"
MARKER = "<!-- browser-qa -->"

# Stands in for the GitHub CLI: serves comments from comments.json, records writes.
FAKE_GH = r"""#!/usr/bin/env python3
import json, os, sys
state = os.environ["FAKE_GH_STATE"]
args = sys.argv[1:]
with open(os.path.join(state, "calls.log"), "a") as log:
    log.write(json.dumps(args) + "\n")
if "--jq" in args:
    comments = json.load(open(os.path.join(state, "comments.json")))
    for c in comments:
        if c["user"]["login"] == "github-actions[bot]" and c["body"].startswith("<!-- browser-qa -->"):
            print(c["id"])
"""


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def env(tmp_path):
    remote = tmp_path / "remote.git"
    git("init", "-q", "--bare", str(remote))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(FAKE_GH)
    gh.chmod(0o755)
    state = tmp_path / "gh"
    state.mkdir()
    (state / "comments.json").write_text("[]")
    out = tmp_path / "qa-out"
    (out / "shots").mkdir(parents=True)
    (out / "comment.md").write_text(MARKER + "\nhello\n")
    return {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "FAKE_GH_STATE": str(state),
        "GH_TOKEN": "t",
        "REPO": "owner/app",
        "PR": "7",
        "SRC": str(out),
        "REMOTE": str(remote),
    }


def publish(env: dict, run_key: str, shots: list[str]) -> list[list[str]]:
    shots_dir = Path(env["SRC"]) / "shots"
    for old in shots_dir.iterdir():
        old.unlink()
    for name in shots:
        (shots_dir / name).write_bytes(b"png")
    log = Path(env["FAKE_GH_STATE"]) / "calls.log"
    log.unlink(missing_ok=True)
    subprocess.run(["bash", str(SCRIPT)], env={**env, "RUN_KEY": run_key}, check=True, capture_output=True)
    return [json.loads(line) for line in log.read_text().splitlines()]


def branch_files(env: dict) -> list[str]:
    out = git("--git-dir", env["REMOTE"], "ls-tree", "-r", "--name-only", "browser-qa-screenshots")
    return sorted(out.split())


def test_first_run_creates_the_branch_and_posts_a_new_comment(env):
    calls = publish(env, "100-1", ["01-smoke-desktop-1.png", "01-smoke-phone-1.png"])

    assert branch_files(env) == ["pr-7/100-1/01-smoke-desktop-1.png", "pr-7/100-1/01-smoke-phone-1.png"]
    writes = [c for c in calls if "--jq" not in c]
    assert writes == [["api", "repos/owner/app/issues/7/comments", "-F", f"body=@{env['SRC']}/comment.md"]]


def test_a_rerun_replaces_the_prs_old_screenshots_and_updates_its_comment(env):
    publish(env, "100-1", ["01-old-desktop-1.png"])
    (Path(env["FAKE_GH_STATE"]) / "comments.json").write_text(
        json.dumps(
            [
                {"id": 5, "user": {"login": "someone"}, "body": MARKER + " quoted by a person"},
                {"id": 9, "user": {"login": "github-actions[bot]"}, "body": MARKER + "\nold"},
            ]
        )
    )
    calls = publish(env, "101-1", ["01-new-desktop-1.png"])

    assert branch_files(env) == ["pr-7/101-1/01-new-desktop-1.png"]
    writes = [c for c in calls if "--jq" not in c]
    assert writes == [
        ["api", "-X", "PATCH", "repos/owner/app/issues/comments/9", "-F", f"body=@{env['SRC']}/comment.md"]
    ]


def test_other_prs_screenshots_are_kept(env):
    publish(env, "100-1", ["01-a-desktop-1.png"])
    publish({**env, "PR": "8"}, "200-1", ["01-b-desktop-1.png"])

    assert branch_files(env) == ["pr-7/100-1/01-a-desktop-1.png", "pr-8/200-1/01-b-desktop-1.png"]


def test_no_screenshots_still_posts_the_comment_without_touching_the_branch(env):
    calls = publish(env, "100-1", [])

    assert git("--git-dir", env["REMOTE"], "branch", "--list") == ""
    assert any(c[:2] == ["api", "repos/owner/app/issues/7/comments"] for c in calls)
