const { test, expect } = require('@playwright/test');

test('ux: hotel cards visible', async ({ page }) => {
  await page.goto('/hotels/');
  await expect(page.locator('.card').first()).toBeVisible();
});
