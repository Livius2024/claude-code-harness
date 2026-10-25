// Browser QA for the app's web UI. Off until this file is renamed to
// playwright.config.ts and START_COMMAND / BASE_URL below are set (README.md).
// CI (.github/workflows/browser-qa.yml) then runs it on every PR and posts the
// screenshots to the PR.
import { defineConfig, devices } from '@playwright/test';

// Starts the app from the repository root; BASE_URL is where it listens.
const START_COMMAND = process.env.START_COMMAND ?? '<e.g. uv run uvicorn app.main:app --port 8000>';
const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:8000';

export default defineConfig({
  testDir: './tests',
  outputDir: './test-results',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [
    ['list'],
    ['json', { outputFile: 'results.json' }],
    ['html', { open: 'never', outputFolder: 'report' }],
  ],
  use: {
    baseURL: BASE_URL,
    // Every check ends with a screenshot; the PR comment shows them.
    screenshot: 'on',
    trace: 'retain-on-failure',
    // A container whose preinstalled Chromium differs from this Playwright version.
    launchOptions: { executablePath: process.env.PW_CHROMIUM_PATH || undefined },
  },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1280, height: 800 } } },
    { name: 'phone', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command: START_COMMAND,
    cwd: '..',
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
