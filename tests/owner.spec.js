const { test, expect } = require('@playwright/test');

async function login(page, email, password = 'Test@123') {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('owner: dashboard lists property', async ({ page }) => {
  await login(page, 'property_owner@test.com');
  await page.goto('/owner/dashboard/');
  await expect(page.getByText('Property Management')).toBeVisible();
  await expect(page.getByText('Aurora Bay Hotel')).toBeVisible();
});
