import { expect, test } from '@playwright/test';

// The home page opens with no server error and no browser console error.
// Each requirement with a screen gets its own spec next to this one, titled
// with its R-ID ("R3 shows the VAT total per month"), so the PR comment maps
// every screenshot to its row in ACCEPTANCE.md.
test('smoke: home page loads without errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  page.on('pageerror', (err) => errors.push(err.message));

  const response = await page.goto('/');
  expect(response?.status(), 'HTTP status of /').toBeLessThan(400);
  await expect(page.locator('body')).toBeVisible();
  expect(errors, 'browser console errors').toEqual([]);
});
