const { test, expect } = require('@playwright/test');

test('payment: invoice not linked on success page', async ({ page }) => {
  await page.goto('/booking/00000000-0000-0000-0000-000000000000/success/');
  await expect(page.getByText('Access denied')).toBeVisible();
});
