const { test, expect } = require('@playwright/test');

test('inventory: booking page requires approved property', async ({ page }) => {
  await page.goto('/hotels/999999/');
  await expect(page.getByText('Property not available')).toBeVisible();
});
