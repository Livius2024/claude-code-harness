import { expect, test } from '../fixtures';

// A requirement that saves data checks the backend too, not only the screen:
// after the UI action, the API (or the project's database helper) must hold it.
test('R2 saves an invoice and the backend stores it', async ({ page, request }, testInfo) => {
  const number = `F-${testInfo.project.name}-${Date.now()}`;
  await page.goto('/invoices.html');
  await page.getByLabel('Număr').fill(number);
  await page.getByLabel('Sumă').fill('1234.56');
  await page.getByRole('button', { name: 'Adaugă' }).click();
  await expect(page.getByRole('status')).toHaveText('Salvat');
  await expect(page.getByText(`${number}: 1234.56`)).toBeVisible();

  const stored = await request.get('/api/invoices');
  expect(stored.status()).toBe(200);
  expect(await stored.json()).toContainEqual({ number, amount: '1234.56' });
});
