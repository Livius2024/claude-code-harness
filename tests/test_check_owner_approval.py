import subprocess
from pathlib import Path

import pytest
from check_owner_approval import main, matches, protected_changes, read_patterns
from conftest import STARTER

PATTERNS = read_patterns(STARTER / ".github" / "owner-approval-paths.txt")


@pytest.mark.parametrize(
    "path",
    [
        "spec.md",
        "AGENTS.md",
        ".github/workflows/ci.yml",
        ".claude/rules/factory.md",
        "docs/domain/vat.md",
        "src/app/tax_rates.py",
        "src/fiscal/rules.py",
        "src/app/vat_tax.py",
        "src/audit/rules/materiality.py",
        "scripts/check_acceptance.py",
        # The backend guard of browser QA and the scripts that judge it (Codex P0, PR #8).
        "scripts/check_e2e_guard.py",
        "scripts/browser_qa_comment.py",
        "e2e/fixtures.ts",
        "e2e/server-log.ts",
        "e2e/playwright.config.ts",
    ],
)
def test_protected_paths(path):
    assert protected_changes([path], PATTERNS) == [path]


@pytest.mark.parametrize(
    "path",
    [
        "src/app/syntax.py",
        "src/app/invoices.py",
        "tests/test_import.py",
        "README.md",
        "ACCEPTANCE.md",
        "e2e/tests/r1.spec.ts",
    ],
)
def test_ordinary_paths(path):
    assert protected_changes([path], PATTERNS) == []


def test_matches_root_and_nested():
    assert matches("rules/x.md", "**/rules/**")
    assert matches("a/b/rules/x.md", "**/rules/**")
    assert matches("docs/domain/a/b.md", "docs/domain/**")
    assert not matches("docs/domains.md", "docs/domain/**")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "README.md").write_text("x\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def commit(repo: Path, path: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("change\n")
    git(repo, "add", ".")
    git(repo, "commit", "-qm", f"change {path}")
    return git(repo, "rev-parse", "HEAD")


def run(repo: Path, base: str, head: str, labels: str = "") -> int:
    patterns = str(STARTER / ".github" / "owner-approval-paths.txt")
    return main(["--base", base, "--head", head, "--labels", labels, "--patterns", patterns])


def test_ordinary_pr_passes(repo):
    base = git(repo, "rev-parse", "HEAD")
    assert run(repo, base, commit(repo, "src/app/invoices.py")) == 0


def test_rule_pr_needs_label(repo, capsys):
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, "src/fiscal/vat.py")
    assert run(repo, base, head) == 1
    assert "Owner approval needed" in capsys.readouterr().out
    assert run(repo, base, head, "bug,owner-approved") == 0


def test_missing_patterns_file_protects_nothing(repo):
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, "spec.md")
    assert main(["--base", base, "--head", head, "--patterns", str(repo / "absent.txt")]) == 0


def test_renaming_a_protected_file_needs_label(repo):
    commit(repo, "spec.md")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "mv", "spec.md", "other.md")
    git(repo, "commit", "-qm", "rename")
    head = git(repo, "rev-parse", "HEAD")
    assert run(repo, base, head) == 1
    assert run(repo, base, head, "owner-approved") == 0


def test_protected_file_with_a_non_ascii_name_needs_label(repo):
    # git quotes and octal-escapes non-ASCII paths unless asked for NUL-separated output.
    base = git(repo, "rev-parse", "HEAD")
    head = commit(repo, "docs/domain/Налог.md")
    assert run(repo, base, head) == 1
    assert run(repo, base, head, "owner-approved") == 0
