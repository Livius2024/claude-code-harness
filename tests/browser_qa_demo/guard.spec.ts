import { expect, test } from '../fixtures';

// Proves the backend guard in fixtures.ts. The first two checks are marked
// test.fail(): they pass only if the guard fails them, so a broken guard turns
// the self-test red.
test.describe('guard', () => {
  test('a failed API call fails the check, even with a good screen', async ({ page }) => {
    test.fail();
    const answered = page.waitForResponse('**/api/missing');
    await page.goto('/invoices.html?call=/api/missing');
    await expect(page.getByRole('heading', { name: 'Facturi (date de test)' })).toBeVisible();
    await answered;
  });

  test('a failed API call in a second tab fails the check too', async ({ context }) => {
    test.fail();
    const tab = await context.newPage();
    const answered = tab.waitForResponse('**/api/missing');
    await tab.goto('/invoices.html?call=/api/missing');
    await answered;
  });

  test('a failed call to the API on another local origin fails the check too', async ({ page, baseURL }) => {
    // Apps whose UI and API listen on different ports (Next.js + FastAPI).
    test.fail();
    const api = baseURL!.replace('127.0.0.1', 'localhost');
    const answered = page.waitForResponse('**/api/missing');
    await page.goto(`/invoices.html?call=${encodeURIComponent(`${api}/api/missing`)}`);
    await answered;
  });

  test('an error in the server log fails the check, even with HTTP 200', async ({ page }) => {
    test.fail();
    const answered = page.waitForResponse('**/api/warn');
    await page.goto('/invoices.html?call=/api/warn');
    await answered;
  });

  test.describe('with an expected failure listed', () => {
    test.use({ allowedHttpErrors: [/\/api\/missing$/] });

    test('allowedHttpErrors lets that one through', async ({ page }) => {
      const answered = page.waitForResponse('**/api/missing');
      await page.goto('/invoices.html?call=/api/missing');
      await answered;
    });
  });
});
