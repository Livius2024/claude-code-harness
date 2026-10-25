import { expect, test } from '../fixtures';

// Each check marked test.fail() passes only if the guard in ../fixtures.ts
// fails it, so a broken guard turns this self-test red. The other checks are
// the controls: a healthy call and an allowed failure must pass.
async function open(page, call: string) {
  const answered = page.waitForEvent('requestfinished', (r) => r.url() === call).catch(() => undefined);
  const failed = page.waitForEvent('requestfailed', (r) => r.url() === call).catch(() => undefined);
  await page.goto(`/?call=${encodeURIComponent(call)}`);
  await expect(page.getByRole('heading', { name: 'Guard self-test' })).toBeVisible();
  await Promise.race([answered, failed]);
}

test('control: a healthy API call passes', async ({ page, baseURL }) => {
  await open(page, `${baseURL}/api/ok`);
});

test('HTTP 404 from the API fails the check', async ({ page, baseURL }) => {
  test.fail();
  await open(page, `${baseURL}/api/missing`);
});

test('a refused connection to a local port fails the check', async ({ page }) => {
  test.fail();
  await open(page, 'http://127.0.0.1:9/api/down');
});

test('a failed call to the API on another local origin fails the check', async ({ page, baseURL }) => {
  test.fail();
  await open(page, `${baseURL!.replace('127.0.0.1', 'localhost')}/api/missing`);
});

test('a failed call in a second tab fails the check', async ({ context, baseURL }) => {
  test.fail();
  await open(await context.newPage(), `${baseURL}/api/missing`);
});

test('an error in the server log fails the check, even with HTTP 200', async ({ page, baseURL }) => {
  test.fail();
  await open(page, `${baseURL}/api/warn`);
});

test.describe('control: an expected failure listed in allowedHttpErrors', () => {
  test.use({ allowedHttpErrors: [/\/api\/missing$/] });

  test('passes', async ({ page, baseURL }) => {
    await open(page, `${baseURL}/api/missing`);
  });
});
