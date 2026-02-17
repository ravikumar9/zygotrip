import { test, expect } from '@playwright/test';

test('global search works and renders results', async ({ page }) => {
  await page.goto('/search/?q=hotel');
  await expect(page.locator('h1')).toContainText('Search Results');
  const cards = page.locator('[data-score]');
  await expect(cards.first()).toBeVisible();
});

test('search ranking sorts by score', async ({ page }) => {
  await page.goto('/search/?q=hotel');
  const scores = await page.locator('[data-score]').evaluateAll((nodes) =>
    nodes.map((node) => Number(node.getAttribute('data-score') || '0'))
  );
  for (let i = 1; i < Math.min(scores.length, 5); i += 1) {
    expect(scores[i]).toBeLessThanOrEqual(scores[i - 1]);
  }
});

test('search input debounces before submitting', async ({ page }) => {
  await page.goto('/search/');
  await page.fill('[data-search-input]', 'hotel');
  await page.waitForTimeout(200);
  expect(page.url()).not.toContain('q=hotel');
  await page.waitForURL(/\?q=hotel/, { timeout: 2000 });
});
