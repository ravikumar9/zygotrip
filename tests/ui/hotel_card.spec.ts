import { test, expect } from '@playwright/test';

test('hotel card shows required fields', async ({ page }) => {
  await page.goto('/hotels/');
  const card = page.locator('.hotel-card').first();
  await expect(card.locator('.card-image')).toBeVisible();
  const bgImage = await card.locator('.card-image').evaluate((el) => {
    return window.getComputedStyle(el).backgroundImage;
  });
  expect(bgImage).not.toBe('none');
  await expect(card.locator('.card-title')).toBeVisible();
  await expect(card.locator('.hotel-type')).toBeVisible();
  await expect(card.locator('.hotel-rating')).toBeVisible();
  await expect(card.locator('.hotel-location')).toBeVisible();
  await expect(card.locator('.hotel-amenities')).toBeVisible();
  await expect(card.locator('.hotel-policies')).toBeVisible();
  await expect(card.locator('.hotel-price')).toBeVisible();
  await expect(card.locator('.price-discount')).toBeVisible();
  await expect(card.locator('a.button-accent')).toBeVisible();
});
