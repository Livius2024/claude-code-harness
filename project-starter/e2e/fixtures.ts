// Every check imports `test` and `expect` from here, not from '@playwright/test'
// (CI runs scripts/check_e2e_guard.py to make sure). On top of what the check
// asserts on the screen, each check then also fails when, while it ran:
// - a request to the app failed: HTTP 4xx/5xx or no response at all;
// - the app's server log (the output of START_COMMAND) shows an error.
// A screenshot shows only the screen; these catch the backend failing behind it.
import { closeSync, existsSync, openSync, readSync, statSync } from 'node:fs';
import { expect, test as base } from '@playwright/test';
import { SERVER_LOG } from './server-log';

export { expect };

// Lines of the server log that count as an error. Override with SERVER_LOG_ERRORS (a regex).
const SERVER_ERROR = new RegExp(
  process.env.SERVER_LOG_ERRORS ??
    String.raw`Traceback \(most recent call last\)|\b(ERROR|CRITICAL|FATAL)\b|Unhandled(Promise)?Rejection|Exception occurred|^panic:`,
  'm',
);
// Servers often log a failure just after sending the response.
const SETTLE_MS = 300;

type Options = {
  // URLs a check expects to fail, e.g. [/\/api\/login$/] in a check of a wrong password.
  allowedHttpErrors: RegExp[];
};

function logSize(): number {
  return existsSync(SERVER_LOG) ? statSync(SERVER_LOG).size : 0;
}

function readLogFrom(start: number): string {
  if (!existsSync(SERVER_LOG)) return '';
  const length = statSync(SERVER_LOG).size - start;
  if (length <= 0) return '';
  const buffer = Buffer.alloc(length);
  const fd = openSync(SERVER_LOG, 'r');
  try {
    readSync(fd, buffer, 0, length, start);
  } finally {
    closeSync(fd);
  }
  return buffer.toString('utf8');
}

export const test = base.extend<Options & { backendGuard: void }>({
  allowedHttpErrors: [[], { option: true }],

  backendGuard: [
    async ({ page, baseURL, allowedHttpErrors }, use) => {
      const origin = baseURL ? new URL(baseURL).origin : '';
      const watched = (url: string) =>
        (!origin || url.startsWith(origin)) && !allowedHttpErrors.some((pattern) => pattern.test(url));
      const failedRequests: string[] = [];
      page.on('response', (response) => {
        if (response.status() >= 400 && watched(response.url())) {
          failedRequests.push(`HTTP ${response.status()} ${response.request().method()} ${response.url()}`);
        }
      });
      page.on('requestfailed', (request) => {
        const reason = request.failure()?.errorText ?? 'failed';
        // A navigation cancels the previous page's pending requests; that is not a backend error.
        if (!reason.includes('ERR_ABORTED') && watched(request.url())) {
          failedRequests.push(`${reason} ${request.method()} ${request.url()}`);
        }
      });
      if (process.env.CI && !existsSync(SERVER_LOG)) {
        throw new Error(`The server log ${SERVER_LOG} is missing: the app's output is not being checked.`);
      }
      const logStart = logSize();

      await use();

      await new Promise((resolve) => setTimeout(resolve, SETTLE_MS));
      const serverErrors = readLogFrom(logStart)
        .split(/\r?\n/)
        .filter((line) => SERVER_ERROR.test(line));
      expect(failedRequests, 'requests to the app that failed (list expected ones in allowedHttpErrors)').toEqual([]);
      expect(serverErrors, `errors in the server log while this check ran (${SERVER_LOG})`).toEqual([]);
    },
    { auto: true },
  ],
});
