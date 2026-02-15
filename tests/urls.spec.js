const { test, expect } = require('@playwright/test');

test('urls: key routes respond', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('link', { name: '✈️ Zygotrip' })).toBeVisible();
  await page.goto('/hotels/');
  await expect(page.getByRole('heading', { name: 'Browse Hotels' })).toBeVisible();
});
