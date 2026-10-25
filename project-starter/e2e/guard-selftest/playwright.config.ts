// Self-test of the backend guard in ../fixtures.ts, independent of the app:
// `npx playwright test -c guard-selftest` from e2e/. CI runs it when the guard
// changes (.github/workflows/browser-qa-guard.yml).
import { defineConfig, devices } from '@playwright/test';
import { SERVER_LOG } from '../server-log';
import { SELFTEST_API_ORIGIN } from './origins';

const PORT = 8799;
process.env.APP_ORIGINS = SELFTEST_API_ORIGIN;

export default defineConfig({
  testDir: '.',
  outputDir: './test-results',
  // One worker: two checks log a server error on purpose, and the guard reads the log by time window.
  workers: 1,
  // A stray test.only() would run just one check and hide the others.
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    launchOptions: { executablePath: process.env.PW_CHROMIUM_PATH || undefined },
  },
  projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `python3 -u guard-selftest/server.py ${PORT} > "${SERVER_LOG}" 2>&1`,
    cwd: '..',
    url: `http://127.0.0.1:${PORT}`,
    reuseExistingServer: false,
    timeout: 60_000,
  },
});
