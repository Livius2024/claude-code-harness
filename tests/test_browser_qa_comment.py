import base64
import json
from pathlib import Path

from browser_qa_comment import MARKER, main

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


def result(status, shot=None, error=None):
    attachments = [{"name": "screenshot", "contentType": "image/png", "path": str(shot)}] if shot else []
    out = {"status": status, "attachments": attachments, "errors": []}
    if error:
        out["errors"] = [{"message": error}]
    return out


def pw_test(project, status, results):
    return {"projectName": project, "status": status, "results": results}


def report(*suites):
    return {"suites": list(suites), "stats": {}}


def file_suite(name, specs=(), suites=()):
    return {"title": name, "file": name, "specs": list(specs), "suites": list(suites)}


def run(tmp_path: Path, data, *extra: str) -> str:
    results = tmp_path / "results.json"
    if data is not None:
        results.write_text(json.dumps(data), encoding="utf-8")
    assert main(["--results", str(results), "--out", str(tmp_path / "out"), *extra]) == 0
    return (tmp_path / "out" / "comment.md").read_text(encoding="utf-8")


def shot(tmp_path: Path, name: str) -> Path:
    path = tmp_path / "test-results" / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(PNG)
    return path


def test_every_check_gets_one_row_with_its_status_per_size_and_its_screenshots(tmp_path):
    # Playwright repeats a spec once per project when fullyParallel is on.
    data = report(
        file_suite(
            "smoke.spec.ts",
            specs=[
                {
                    "title": "smoke: home page loads",
                    "tests": [pw_test("desktop", "expected", [result("passed", shot(tmp_path, "d"))])],
                },
                {
                    "title": "smoke: home page loads",
                    "tests": [pw_test("phone", "expected", [result("passed", shot(tmp_path, "p"))])],
                },
            ],
        )
    )
    comment = run(tmp_path, data, "--image-base", "https://github.com/o/r/blob/qa/pr-7/1-1", "--sha", "abcdef1234")

    assert comment.startswith(MARKER)
    assert "## ✅ Browser QA" in comment
    assert "| smoke: home page loads | smoke | ✅ PASS | ✅ PASS |" in comment
    assert "Commit `abcdef1`" in comment
    shots = sorted(p.name for p in (tmp_path / "out" / "shots").iterdir())
    assert shots == ["01-smoke-home-page-loads-desktop-1.png", "01-smoke-home-page-loads-phone-1.png"]
    assert 'src="https://github.com/o/r/blob/qa/pr-7/1-1/01-smoke-home-page-loads-desktop-1.png?raw=true"' in comment


def test_a_failed_check_turns_the_comment_red_and_shows_the_error_without_colour_codes(tmp_path):
    error = 'Error: \x1b[2mexpect(\x1b[22mlocator).toHaveText failed\nExpected: "999,00"\nReceived: "700,00"'
    data = report(
        file_suite(
            "vat.spec.ts",
            suites=[
                {
                    "title": "reports",
                    "file": "vat.spec.ts",
                    "specs": [
                        {
                            "title": "R2 shows the VAT total",
                            "tests": [
                                pw_test("desktop", "unexpected", [result("failed", shot(tmp_path, "f"), error)]),
                                pw_test("phone", "expected", [result("passed")]),
                            ],
                        }
                    ],
                }
            ],
        )
    )
    comment = run(tmp_path, data)

    assert "## ❌ Browser QA" in comment
    assert "❌ FAIL 1" in comment
    assert "| reports › R2 shows the VAT total | R2 | ❌ FAIL | ✅ PASS |" in comment
    assert 'Received: "700,00"' in comment
    assert "\x1b" not in comment
    # Without --image-base the shots are linked relative to the output folder.
    assert 'src="shots/01-reports-r2-shows-the-vat-total-desktop-1.png"' in comment


def test_flaky_counts_as_not_green(tmp_path):
    data = report(
        file_suite(
            "a.spec.ts",
            specs=[
                {"title": "R1 imports", "tests": [pw_test("desktop", "flaky", [result("failed"), result("passed")])]}
            ],
        )
    )
    comment = run(tmp_path, data)

    assert "## ❌ Browser QA" in comment
    assert "⚠️ FLAKY 1" in comment


def test_screenshots_attached_as_body_are_written_out(tmp_path):
    body = base64.b64encode(PNG).decode()
    attachment = {"name": "step", "contentType": "image/png", "body": body}
    data = report(
        file_suite(
            "a.spec.ts",
            specs=[
                {
                    "title": "R1 imports",
                    "tests": [pw_test("desktop", "expected", [{"status": "passed", "attachments": [attachment]}])],
                }
            ],
        )
    )
    run(tmp_path, data)

    assert (tmp_path / "out" / "shots" / "01-r1-imports-desktop-1.png").read_bytes() == PNG


def test_a_missing_report_is_neverificat_not_a_pass(tmp_path):
    comment = run(tmp_path, None, "--run-url", "https://example.test/run/1")

    assert comment.startswith(MARKER)
    assert "NEVERIFICAT" in comment
    assert "PASS" not in comment
    assert "[run log](https://example.test/run/1)" in comment


def test_no_checks_is_not_green(tmp_path):
    comment = run(tmp_path, report(file_suite("empty.spec.ts")))

    assert "## ❌ Browser QA" in comment
    assert "No checks found" in comment
