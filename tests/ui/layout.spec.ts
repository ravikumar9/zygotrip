import { test, expect } from '@playwright/test';

test('hotels and cabs use different base layouts', async ({ page }) => {
  await page.goto('/hotels/');
  await expect(page.locator('body')).toHaveClass(/hotels-shell/);
  await page.goto('/cabs/');
  await expect(page.locator('body')).toHaveClass(/cabs-shell/);
});


test('hotels layout structure renders', async ({ page }) => {
  await page.goto('/hotels/');
  await expect(page.locator('.hotels-header')).toBeVisible();
  await expect(page.locator('.hotels-filters')).toBeVisible();
  await expect(page.locator('.hotels-grid')).toBeVisible();
  const pagination = page.locator('.pagination');
  if (await pagination.count()) {
    await expect(pagination).toBeVisible();
  }
});

test('hotels grid uses 2 columns on desktop', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto('/hotels/');
  const gridTemplate = await page.locator('.hotels-grid').evaluate((el) => {
    return window.getComputedStyle(el).gridTemplateColumns;
  });
  expect(gridTemplate.split(' ').length).toBe(2);
});

test('hotels grid collapses on tablet and mobile', async ({ page }) => {
  await page.setViewportSize({ width: 900, height: 800 });
  await page.goto('/hotels/');
  const tabletTemplate = await page.locator('.hotels-grid').evaluate((el) => {
    return window.getComputedStyle(el).gridTemplateColumns;
  });
  expect(tabletTemplate.split(' ').length).toBe(1);

  await page.setViewportSize({ width: 375, height: 800 });
  await page.reload();
  const mobileTemplate = await page.locator('.hotels-grid').evaluate((el) => {
    return window.getComputedStyle(el).gridTemplateColumns;
  });
  expect(mobileTemplate.split(' ').length).toBe(1);
});
