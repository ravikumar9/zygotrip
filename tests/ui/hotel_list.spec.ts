import { test, expect } from '@playwright/test';

test('hotel list renders cards grid', async ({ page }) => {
  await page.goto('/hotels/');
  const cards = page.locator('.hotel-card');
  await expect(cards.first()).toBeVisible();
});


test('hotel filters visible and apply', async ({ page }) => {
  await page.goto('/hotels/');
  await page.locator('input[name="city"][value="delhi"]').check();
  await page.locator('button:has-text("Apply Filters")').click();
  await expect(page).toHaveURL(/city=delhi/);
});
