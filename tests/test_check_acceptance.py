import shutil
from pathlib import Path

import pytest
from check_acceptance import check, main
from conftest import STARTER

HEADER = (
    "| ID | Requirement (owner's words) | Verifiable criterion | Command or browser scenario"
    " | Status | SHA | Evidence |\n|---|---|---|---|---|---|---|\n"
)


def project(tmp_path: Path, spec: str | None, rows: str) -> Path:
    if spec is not None:
        (tmp_path / "spec.md").write_text(spec, encoding="utf-8")
    (tmp_path / "ACCEPTANCE.md").write_text("# ACCEPTANCE\n\n" + HEADER + rows, encoding="utf-8")
    return tmp_path


SPEC = (
    "# Spec\n\n## Requirements\n\n- R1: Import invoices\n- **R2**: VAT total per month\n"
    "\n## Non-goals\n\n- R9: not a requirement\n"
)
ROW_R1 = (
    "| R1 | Import invoices | totals match | `uv run pytest tests/test_import.py`"
    " | PASS | abc1234 | .scratch/evidence/R1/out.txt |\n"
)
ROW_R2 = "| R2 | VAT total | matches worked example | `uv run pytest tests/test_vat.py` | NEVERIFICAT | | |\n"


def test_fresh_starter_passes():
    errors, notes = check(STARTER)
    assert errors == []
    assert "spec.md does not exist" in notes[0]


def test_matching_manifest_passes(tmp_path):
    errors, _ = check(project(tmp_path, SPEC, ROW_R1 + ROW_R2))
    assert errors == []


def test_requirement_without_row_fails(tmp_path):
    errors, _ = check(project(tmp_path, SPEC, ROW_R1))
    assert errors == ["R2 is in spec.md but has no ACCEPTANCE.md row"]


def test_ids_outside_requirements_section_are_ignored(tmp_path):
    errors, _ = check(project(tmp_path, SPEC, ROW_R1 + ROW_R2))
    assert not any("R9" in e for e in errors)


def test_orphan_and_duplicate_rows_fail(tmp_path):
    orphan = ROW_R2.replace("| R2 |", "| R3 |")
    errors, _ = check(project(tmp_path, SPEC, ROW_R1 + ROW_R2 + ROW_R2 + orphan))
    assert any("R2 already has a row" in e for e in errors)
    assert any("R3 is not in spec.md" in e for e in errors)


def test_duplicate_manifest_id_fails(tmp_path):
    spec = SPEC.replace("- **R2**", "- R1: again\n- **R2**")
    errors, _ = check(project(tmp_path, spec, ROW_R1 + ROW_R2))
    assert any("R1 is listed twice" in e for e in errors)


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("`uv run pytest tests/test_import.py`", "<command>", "PASS without a command"),
        ("abc1234", "", "PASS without the SHA"),
        (".scratch/evidence/R1/out.txt", "", "PASS without an evidence path"),
        ("| PASS |", "| DONE |", "status `DONE`"),
        ("totals match", "<criterion>", "no verifiable criterion"),
    ],
)
def test_row_rules(tmp_path, old, new, message):
    errors, _ = check(project(tmp_path, SPEC, ROW_R1.replace(old, new) + ROW_R2))
    assert any(message in e for e in errors), errors


def test_starter_placeholder_rows_fail_once_spec_exists(tmp_path):
    shutil.copy(STARTER / "ACCEPTANCE.md", tmp_path / "ACCEPTANCE.md")
    (tmp_path / "spec.md").write_text(SPEC, encoding="utf-8")
    errors, _ = check(tmp_path)
    assert any("no verifiable criterion" in e for e in errors)


def test_spec_without_requirements_fails(tmp_path):
    errors, _ = check(project(tmp_path, "# Spec\n\nNothing here.\n", ""))
    assert any("no requirements" in e for e in errors)


def test_missing_acceptance_fails(tmp_path):
    (tmp_path / "spec.md").write_text(SPEC, encoding="utf-8")
    errors, _ = check(tmp_path)
    assert errors == ["ACCEPTANCE.md is missing but spec.md exists"]


def test_main_exit_codes(tmp_path):
    assert main(["--root", str(project(tmp_path, SPEC, ROW_R1 + ROW_R2))]) == 0
    assert main(["--root", str(project(tmp_path, SPEC, ROW_R1))]) == 1
