# Browser QA (e2e/)

Playwright checks of the app's web UI, at desktop (1280×800) and phone (Pixel 7) size. On every PR, `.github/workflows/browser-qa.yml` starts the app, runs these checks and posts a comment on the PR with the result and one screenshot per check and size. The full HTML report, traces of failures and the screenshots are also in the run's `browser-qa` artifact (14 days).

It is **off** until `e2e/playwright.config.ts` exists. Until then the `browser-qa` job passes without doing anything. A project without a web UI leaves it off.

## Turn it on

1. Rename `playwright.config.example.ts` to `playwright.config.ts`.
2. Set `START_COMMAND` (starts the app from the repository root) and `BASE_URL` (where it listens), e.g. `uv run uvicorn app.main:app --port 8000` and `http://127.0.0.1:8000`.
3. CI installs the app the same way as the `checks` job (`uv sync` for `pyproject.toml`, `npm ci`/`pnpm install` for `package.json`). Anything else the app needs before it starts (seed a demo database, copy `.env.example` to `.env`) goes in `e2e/setup.sh`, which CI runs when it exists.

## Write a check per requirement

One spec file per requirement that has a screen, in `tests/`, titled with its R-ID:

```ts
import { expect, test } from '@playwright/test';

test('R2 shows the VAT total per month', async ({ page }) => {
  await page.goto('/reports/vat');
  await page.getByLabel('Month').selectOption('2026-09');
  await expect(page.getByTestId('vat-total')).toHaveText('1 234,56');
});
```

- Check the criterion written in `ACCEPTANCE.md`, not only that the page opens.
- Use fake data only (fixtures in the repo). The screenshots are published on the PR, and on a public repository anyone can see them.
- The `ACCEPTANCE.md` row's command is then `npx --prefix e2e playwright test -g R2`.

## Run it locally (or in a thread) before opening a PR

```
cd e2e
npm ci
npx playwright install chromium   # once; skip where Chromium is preinstalled
npx playwright test               # starts the app itself
npx playwright show-report report # optional: the HTML report
```

Screenshots are in `test-results/<check>-<size>/test-finished-1.png`. `python3 scripts/browser_qa_comment.py --results e2e/results.json --out qa-out` writes the same comment CI posts, to `qa-out/comment.md`.

If the container has Chromium preinstalled for another Playwright version, point `PW_CHROMIUM_PATH` at that Chromium binary.
