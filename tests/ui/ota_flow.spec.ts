import { test, expect } from '@playwright/test';

function formatDate(offsetDays: number) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return date.toISOString().slice(0, 10);
}

test('ota flow: register, login, search, book, logout', async ({ page }) => {
  const email = `user${Date.now()}@test.com`;
  const password = 'Test@1234';

  await page.goto('/register/');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="full_name"]', 'Playwright User');
  await page.fill('input[name="password1"]', password);
  await page.fill('input[name="password2"]', password);
  await page.getByRole('button', { name: 'Create Account' }).click();
  await expect(page.getByText('Logout')).toBeVisible();

  await page.goto('/logout/');
  await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible();

  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByText('Logout')).toBeVisible();

  const searchQuery = 'Hyderabad';
  await page.goto(`/search/?q=${encodeURIComponent(searchQuery)}`);
  await expect(page.locator('.hotel-card-cta').first()).toBeVisible({ timeout: 8000 });
  await page.locator('.hotel-card-cta').first().click();
  await page.waitForURL(/\/hotels\//, { timeout: 8000 });

  const apiResponse = await page.request.get(`/search/?q=${encodeURIComponent(searchQuery)}&format=json`);
  const apiPayload = await apiResponse.json();
  const propertyId = apiPayload?.results?.[0]?.id;
  expect(propertyId).toBeTruthy();
  await page.goto(`/booking/property/${propertyId}/`);
  await page.selectOption('select[name="room_type"]', { index: 1 });
  await page.fill('input[name="check_in"]', formatDate(1));
  await page.fill('input[name="check_out"]', formatDate(3));
  await page.fill('input[name="quantity"]', '1');
  await page.fill('input[name="guest_full_name"]', 'Playwright User');
  await page.fill('input[name="guest_age"]', '30');
  await page.getByRole('button', { name: 'Continue to Review' }).click();
  await page.waitForURL(/\/booking\/.+\/review\//, { timeout: 5000 });
  await expect(page.getByText('Review Your Booking')).toBeVisible();

  await page.getByRole('button', { name: 'Proceed to Payment' }).click();
  await page.waitForURL(/\/booking\/.+\/payment\//, { timeout: 5000 });
  await page.getByRole('button', { name: 'Complete Payment' }).click();
  await page.waitForURL(/\/booking\/.+\/success\//, { timeout: 5000 });
  await expect(page.getByText('Booking Confirmed!')).toBeVisible();

  await page.getByText('Logout').click();
  await expect(page.getByRole('link', { name: 'Login', exact: true })).toBeVisible();
});
