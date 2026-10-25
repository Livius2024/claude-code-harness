from pathlib import Path

from check_e2e_guard import main


def spec(root: Path, name: str, body: str) -> Path:
    path = root / "e2e" / "tests" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def fixtures(root: Path) -> None:
    (root / "e2e").mkdir(parents=True, exist_ok=True)
    (root / "e2e" / "fixtures.ts").write_text("export const test = 1;\n", encoding="utf-8")


def test_specs_that_import_the_guarded_test_pass(tmp_path, capsys):
    fixtures(tmp_path)
    spec(tmp_path, "smoke.spec.ts", "import { expect, test } from '../fixtures';\n")
    spec(tmp_path, "nested/r2.spec.ts", 'import { test } from "../../fixtures";\n')
    assert main(["--root", str(tmp_path)]) == 0


def test_a_spec_importing_playwright_directly_bypasses_the_backend_guard_and_fails(tmp_path, capsys):
    fixtures(tmp_path)
    spec(tmp_path, "smoke.spec.ts", "import { expect, test } from '../fixtures';\n")
    spec(tmp_path, "r3.spec.ts", "import { test, expect } from '@playwright/test';\n")
    spec(tmp_path, "r4.spec.js", 'const { test } = require("@playwright/test");\n')
    assert main(["--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "r3.spec.ts" in out and "r4.spec.js" in out and "smoke.spec.ts" not in out


def test_type_only_imports_from_playwright_are_allowed(tmp_path):
    fixtures(tmp_path)
    spec(tmp_path, "r5.spec.ts", "import type { Page } from '@playwright/test';\nimport { test } from '../fixtures';\n")
    assert main(["--root", str(tmp_path)]) == 0


def test_missing_fixtures_file_fails(tmp_path, capsys):
    spec(tmp_path, "smoke.spec.ts", "import { test } from '../fixtures';\n")
    assert main(["--root", str(tmp_path)]) == 1
    assert "fixtures.ts" in capsys.readouterr().out


def test_the_starter_itself_passes():
    starter = Path(__file__).resolve().parent.parent / "project-starter"
    assert main(["--root", str(starter)]) == 0


def test_a_helper_that_re_exports_playwrights_test_fails(tmp_path, capsys):
    # Codex P0 on PR #8: a spec importing `test` from a helper outside e2e/tests.
    fixtures(tmp_path)
    (tmp_path / "e2e" / "plain-test.ts").write_text("export { test } from '@playwright/test';\n", encoding="utf-8")
    (tmp_path / "e2e" / "lib").mkdir()
    (tmp_path / "e2e" / "lib" / "deep.ts").write_text("import { test } from 'playwright/test';\n", encoding="utf-8")
    spec(tmp_path, "r6.spec.ts", "import { test } from '../plain-test';\n")
    assert main(["--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "e2e/plain-test.ts" in out and "e2e/lib/deep.ts" in out


def test_the_config_fixtures_and_installed_packages_may_import_playwright(tmp_path):
    fixtures(tmp_path)
    (tmp_path / "e2e" / "fixtures.ts").write_text(
        "import { test as base } from '@playwright/test';\n", encoding="utf-8"
    )
    (tmp_path / "e2e" / "playwright.config.ts").write_text(
        "import { defineConfig } from '@playwright/test';\n", encoding="utf-8"
    )
    module = tmp_path / "e2e" / "node_modules" / "@playwright" / "test" / "index.js"
    module.parent.mkdir(parents=True)
    module.write_text("module.exports = require('playwright/test');\n", encoding="utf-8")
    spec(tmp_path, "smoke.spec.ts", "import { test } from '../fixtures';\n")
    assert main(["--root", str(tmp_path)]) == 0
