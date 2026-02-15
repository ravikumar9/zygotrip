const { test, expect } = require('@playwright/test');

async function login(page, email, password = 'Test@123') {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('refund: finance dashboard blocked for customer', async ({ page }) => {
  await login(page, 'customer@test.com');
  await page.goto('/finance/dashboard/');
  await expect(page.getByText('Access denied')).toBeVisible();
});
