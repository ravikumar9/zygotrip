const { test, expect } = require('@playwright/test');

const users = {
  customer: 'customer@test.com',
};

async function login(page, email, password = 'Test@123') {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

test('auth: login and logout', async ({ page }) => {
  await login(page, users.customer);
  // Open the user dropdown menu first
  await page.click('button.dropdown-trigger');
  await expect(page.getByText('Logout')).toBeVisible();
  await page.getByText('Logout').click();
  await expect(page.getByRole('link', { name: 'Login', exact: true })).toBeVisible();
});
