import json
import os
import shlex
import sys
import time
from pathlib import Path

import pytest
from check_done import dependency_names, main, missing_tool, no_tests_ran, quote

# cmd.exe on Windows understands only double quotes; sh elsewhere.
PY = f'"{sys.executable}"' if os.name == "nt" else shlex.quote(sys.executable)
OK = f"{PY} -c pass"
BAD = f"{PY} -c \"import sys; print('boom'); sys.exit(3)\""


def config(root: Path, checks: list[dict], **extra) -> Path:
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "done.json").write_text(json.dumps({"checks": checks, **extra}), encoding="utf-8")
    return root


def four(**overrides: str | dict) -> list[dict]:
    checks = []
    for name in ("Tests", "Lint", "Typecheck", "Build"):
        value = overrides.get(name, OK)
        checks.append({"name": name, **value} if isinstance(value, dict) else {"name": name, "run": value})
    return checks


def run(root: Path, *args: str) -> int:
    return main(["--root", str(root), *args])


def test_all_four_passing_is_done(tmp_path, capsys):
    assert run(config(tmp_path, four())) == 0
    out = capsys.readouterr().out
    assert "DONE: every check passed." in out
    assert out.count("PASS") == 4


def test_a_failing_check_is_not_done_and_shows_its_output(tmp_path, capsys):
    assert run(config(tmp_path, four(Lint=BAD))) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out and "exited 3" in out and "boom" in out
    assert "NOT DONE" in out and "DONE: every" not in out


def test_a_missing_tool_is_neverificat_not_passed(tmp_path, capsys):
    assert run(config(tmp_path, four(Typecheck="no-such-tool-xyz --check"))) == 2
    out = capsys.readouterr().out
    assert "NEVERIFICAT" in out and "`no-such-tool-xyz` is not installed" in out


def test_a_failure_wins_over_neverificat(tmp_path):
    assert run(config(tmp_path, four(Typecheck="no-such-tool-xyz", Build=BAD))) == 1


def test_a_check_for_another_os_is_neverificat(tmp_path, capsys):
    other = "darwin" if sys.platform.startswith("linux") else "linux"
    assert run(config(tmp_path, four(Build={"run": OK, "os": other}))) == 2
    assert f"needs {other}" in capsys.readouterr().out


def test_a_python_module_that_is_not_installed_is_neverificat(tmp_path, capsys):
    assert run(config(tmp_path, four(Lint=f"{PY} -m no_such_module_xyz check ."))) == 2
    assert "module `no_such_module_xyz` is not installed" in capsys.readouterr().out


def test_pytest_collecting_no_tests_is_neverificat(tmp_path, capsys):
    assert run(config(tmp_path, four(Tests=f"{PY} -m pytest -q -p no:cacheprovider"))) == 2
    assert "collected no tests" in capsys.readouterr().out


def test_a_timeout_is_neverificat_and_stops_the_command(tmp_path, capsys):
    slow = f'{PY} -c "import time; time.sleep(30)"'
    started = time.monotonic()
    assert run(config(tmp_path, four(Tests=slow), timeoutSec=1)) == 2
    assert time.monotonic() - started < 20
    assert "timed out after 1s" in capsys.readouterr().out


@pytest.mark.parametrize("source, expected", [(OK, 0), (BAD, 1)])
def test_a_covered_check_takes_the_status_of_the_check_that_covers_it(tmp_path, capsys, source, expected):
    checks = four(Build=source, Typecheck={"covered_by": "Build", "why": "the compiler checks types"})
    assert run(config(tmp_path, checks)) == expected
    out = capsys.readouterr().out
    assert "(in Build: the compiler checks types)" in out
    assert out.count("FAIL" if expected else "PASS") == (2 if expected else 4)


def test_not_applicable_is_shown_and_does_not_block(tmp_path, capsys):
    assert run(config(tmp_path, four(Typecheck={"not_applicable": "plain JavaScript"}))) == 0
    assert "N/A" in capsys.readouterr().out


@pytest.mark.parametrize(
    "checks, message",
    [
        (four()[:3], "no Build check"),
        ([], "no checks"),
        ([*four(), {"name": "Lint", "stack": "Python", "run": OK}], "stack 'Python' has no Tests, Typecheck, Build"),
        ([*four(), {"name": "Deploy", "run": OK}], "name must be one of"),
        (four(Typecheck={"covered_by": "Build"}), '"covered_by" needs a "why"'),
        (four(Typecheck={"covered_by": "Lint", "why": "x"}, Lint={"not_applicable": "x"}), "which has no command"),
        (four(Lint={"run": OK, "not_applicable": "x"}), "exactly one of"),
        (four(Lint={"not_applicable": " "}), "needs the reason"),
        (four(Lint={"run": [""]}), "non-empty command"),
        (four(Lint={"run": []}), "non-empty command"),
        (four(Lint={"covered_by": None, "why": "x"}), '"covered_by" must name another'),
        (four(Lint={"covered_by": "Lint", "why": "x"}), '"covered_by" must name another'),
        (four(Lint={"covered_by": "Build", "why": None}), '"covered_by" needs a "why"'),
        (four(Lint={"not_applicable": None}), "needs the reason"),
        (four(Lint={"stack": "x"}), "exactly one of"),
    ],
)
def test_a_config_that_drops_or_bends_a_check_is_rejected(tmp_path, capsys, checks, message):
    assert run(config(tmp_path, checks)) == 1
    assert message in capsys.readouterr().out


def test_unset_env_hides_variables_from_the_checks(tmp_path, monkeypatch):
    monkeypatch.setenv("REAL_DATA_PATH", "x")
    monkeypatch.setenv("KEEP_ME", "y")
    hidden = "'REAL_DATA_PATH' not in os.environ and 'KEEP_ME' in os.environ"
    probe = f'{PY} -c "import os, sys; sys.exit(0 if {hidden} else 1)"'
    assert run(config(tmp_path, four(Tests=probe), unsetEnv=["REAL_DATA_*"])) == 0
    assert run(config(tmp_path, four(Tests=probe))) == 1


def listed(root: Path, capsys) -> str:
    assert run(root, "--list") == 0
    return capsys.readouterr().out


def test_a_python_project_gets_pytest_ruff_pyright_and_a_build(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    out = listed(tmp_path, capsys)
    assert "pytest -q" in out and "ruff check ." in out and "ruff format --check ." in out
    assert "pyright" in out and "compileall" in out


def test_a_python_project_with_mypy_settings_and_a_build_system_uses_them(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["hatchling"]\n[tool.mypy]\nstrict = true\n', encoding="utf-8"
    )
    out = listed(tmp_path, capsys)
    assert "mypy ." in out and "pyright" not in out and "build --out" in out


def test_a_plain_javascript_project_has_no_typecheck_to_run(tmp_path, capsys):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"test": "x", "lint": "x"}}), encoding="utf-8")
    out = listed(tmp_path, capsys)
    assert "npm run test" in out and "npm run build" in out and "(not applicable)" in out


def test_a_typescript_project_uses_its_typecheck_script_or_tsc(tmp_path, capsys):
    (tmp_path / "pnpm-lock.yaml").write_text("", encoding="utf-8")
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert "pnpm exec tsc --noEmit" in listed(tmp_path, capsys)
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"type-check": "tsc"}}), encoding="utf-8")
    assert "pnpm run type-check" in listed(tmp_path, capsys)


def test_go_and_dotnet_projects_get_their_own_four_checks(tmp_path, capsys):
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "App.sln").write_text("", encoding="utf-8")
    out = listed(tmp_path, capsys)
    for command in ("go test ./...", "golangci-lint run", "go vet ./...", "go build ./..."):
        assert command in out
    sln = quote("src/App.sln")  # cmd.exe quoting on Windows
    assert f"dotnet test {sln}" in out and f"dotnet format {sln} --verify-no-changes" in out
    assert "(in Build: the C# compiler checks types while it builds)" in out


def test_no_stack_and_no_config_is_neverificat_unless_allowed(tmp_path, capsys):
    assert run(tmp_path) == 2
    assert "nothing was verified" in capsys.readouterr().out
    assert run(tmp_path, "--allow-empty") == 0


def test_allow_empty_does_not_excuse_an_empty_config(tmp_path, capsys):
    assert run(config(tmp_path, []), "--allow-empty") == 1
    assert "no checks" in capsys.readouterr().out


def test_the_config_wins_over_detection(tmp_path, capsys):
    (tmp_path / "go.mod").write_text("module x\n", encoding="utf-8")
    config(tmp_path, four())
    assert "go test" not in listed(tmp_path, capsys)


@pytest.mark.skipif(os.name == "nt", reason="exercises the POSIX shell")
def test_the_starter_itself_passes_with_allow_empty():
    starter = Path(__file__).resolve().parent.parent / "project-starter"
    assert run(starter, "--allow-empty") == 0


@pytest.mark.parametrize(
    "command, out, empty",
    [
        ("go test ./...", "?   \texample.com/x\t[no test files]\n", True),
        ("go test ./...", "ok  \texample.com/x\t0.01s\n?   \texample.com/y\t[no test files]\n", False),
        ("go test ./...", "ok  \texample.com/x\t(cached)\n", False),
        ("dotnet test App.sln", "No test is available in App.Tests.dll.\n", True),
        ("dotnet test App.sln", "Passed!  - Failed: 0, Passed: 12, Skipped: 0, Total: 12\n", False),
        ("python -m pytest", "", False),
        ("go test -json ./...", '{"Action":"skip","Package":"x"}\n', True),
        (
            "go test -json ./...",
            '{"Action":"run","Package":"x","Test":"TestA"}\n{"Action":"pass","Package":"x","Test":"TestA"}\n',
            False,
        ),
    ],
)
def test_runners_that_exit_0_without_running_a_test_are_caught(command, out, empty):
    assert no_tests_ran(command, out) is empty


def test_tools_count_as_installed_only_when_a_plain_uv_sync_installs_them():
    pyproject = {
        "project": {"dependencies": ["httpx>=0.27"], "optional-dependencies": {"lint": ["ruff"]}},
        "dependency-groups": {"dev": ["pytest[cov]>=8", {"include-group": "x"}], "types": ["pyright"]},
        "tool": {"pyright": {}, "mypy": {}},
    }
    assert dependency_names(pyproject) == {"httpx", "pytest"}
    pyproject["tool"]["uv"] = {"default-groups": ["types"]}
    assert dependency_names(pyproject) == {"httpx", "pyright"}
    pyproject["tool"]["uv"] = {"default-groups": "all"}
    assert dependency_names(pyproject) == {"httpx", "pytest", "pyright"}


def test_a_relative_executable_is_looked_up_from_the_project_root(tmp_path):
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "check").write_text("", encoding="utf-8")
    assert missing_tool("bin/check --all", tmp_path) is None
    assert missing_tool("bin/absent --all", tmp_path) == "bin/absent"


def test_a_quoted_executable_path_is_found():
    assert missing_tool(f'"{sys.executable}" -c pass') is None
