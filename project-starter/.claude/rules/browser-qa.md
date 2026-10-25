# Browser QA (projects with a web UI)

This file has no `paths:` on purpose, so every thread loads it. It applies once `e2e/playwright.config.ts` exists; how to turn it on and write checks is in `e2e/README.md`. CI runs the same checks on every PR (`.github/workflows/browser-qa.yml`, job `browser-qa`) and posts a comment with one screenshot per check at desktop and phone size.

- **Turn it on with the first screen.** In a project with a web UI, the first ticket that adds a page renames `e2e/playwright.config.example.ts` to `e2e/playwright.config.ts` and sets the start command and URL. A project without a web UI leaves it off.
- **One check per requirement with a screen.** A spec in `e2e/tests/` titled with its R-ID ("R3 shows the VAT total per month") that checks the criterion in `ACCEPTANCE.md`, not only that the page opens. Its `ACCEPTANCE.md` command is `npx --prefix e2e playwright test -g R3`.
- **Fake data only.** Screenshots are published on the PR (and on a public repository anyone can see them). Never point a check at real client data or real credentials.
- **Before opening a PR that changes the UI,** run the checks yourself: `cd e2e && npm ci && npx playwright test`. Then open the screenshots in `e2e/test-results/` and look at them at both sizes; a green run with a broken-looking screen is not done.
- **After CI,** read the `browser-qa` comment on the PR. A failing check or a visibly wrong screen is fixed in this PR, like any failing test.
- **Did not run = NEVERIFICAT.** If Chromium is missing or the app does not start, say so under "Not verified" in the PR with the reason, and leave the `ACCEPTANCE.md` row NEVERIFICAT. Never mark an R-ID PASS from a browser check that did not run.
- Never delete, skip (`test.skip`, `test.fixme`) or loosen a browser check to get green.
