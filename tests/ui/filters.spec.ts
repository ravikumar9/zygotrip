import { test, expect } from '@playwright/test';

test('hotel filters apply and update URL params', async ({ page }) => {
  await page.goto('/hotels/');
  await expect(page.locator('.hotels-filters')).toBeVisible();
  const initialCards = await page.locator('.hotel-card').count();
  await page.locator('input[name="city"]').first().check();
  await page.locator('button:has-text("Apply Filters")').click();
  await expect(page).toHaveURL(/city=/);
  const filteredCards = await page.locator('.hotel-card').count();
  expect(filteredCards).not.toBe(0);
  expect(filteredCards).not.toBeUndefined();
  expect(initialCards).not.toBeUndefined();
});
