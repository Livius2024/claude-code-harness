import { expect, test } from '../fixtures';

// Demo requirement for the harness self-test: the fake numbers in index.html.
test('R1 shows the VAT total for the period', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByTestId('vat-total')).toHaveText('700,00');
});
