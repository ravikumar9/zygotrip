const { test, expect } = require('@playwright/test');

async function login(page, email, password = 'Test@123') {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
}

function formatDate(date) {
  return date.toISOString().slice(0, 10);
}

function addDays(days) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return formatDate(date);
}

test('invoice: accessible from profile after booking', async ({ page }) => {
  await login(page, 'customer@test.com');
  await page.goto('/hotels/');
  await page.getByRole('link', { name: 'Proceed to Booking' }).first().click();
  await page.selectOption('select[name="room_type"]', { index: 1 });
  await page.fill('input[type="date"] >> nth=0', addDays(4));
  await page.fill('input[type="date"] >> nth=1', addDays(5));
  await page.fill('input[name="guest_full_name"]', 'Invoice User');
  await page.fill('input[name="guest_age"]', '31');
  await page.getByRole('button', { name: 'Proceed to Booking' }).click();
  await page.waitForURL(/\/booking\/.*\/review\//);
  await page.getByRole('button', { name: 'Proceed to Payment' }).click();
  await page.waitForURL(/\/booking\/.*\/payment\//);
  await page.getByRole('button', { name: 'Complete Payment' }).click();
  await page.waitForURL(/\/booking\/.*\/success\//);
  await page.goto('/accounts/profile/');
  await expect(page.getByText('Your Profile')).toBeVisible();
  await page.getByRole('link', { name: 'View Invoice' }).first().click();
  await expect(page.getByRole('heading', { name: 'Invoice' })).toBeVisible();
});
