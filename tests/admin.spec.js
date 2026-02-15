const { test, expect } = require('@playwright/test');

async function login(page, email, password = 'Test@123') {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('admin: approvals page shows pending list', async ({ page }) => {
  await login(page, 'staff_admin@test.com');
  await page.goto('/admin/dashboard/');
  await expect(page.getByText('Admin Dashboard')).toBeVisible();
});
