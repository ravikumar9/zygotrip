import { test, expect } from '@playwright/test';

test('owner dashboard requires login', async ({ page }) => {
  await page.goto('/owner/dashboard/');
  await expect(page).toHaveURL(/accounts\/login/);
});
