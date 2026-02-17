import { test, expect } from '@playwright/test';

test('layout guard: container, sidebar, card widths', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 720 });
  await page.goto('/hotels/', { waitUntil: 'networkidle' });

  const container = page.locator('.container').first();
  const sidebar = page.locator('aside').first();
  const card = page.locator('.hotel-card').first();

  await expect(container).toBeVisible();
  await expect(sidebar).toBeVisible();
  await expect(card).toBeVisible();

  const containerBox = await container.boundingBox();
  const sidebarBox = await sidebar.boundingBox();
  const cardBox = await card.boundingBox();

  const containerWidth = Math.round(containerBox?.width || 0);
  const sidebarWidth = Math.round(sidebarBox?.width || 0);
  const cardWidth = Math.round(cardBox?.width || 0);

  expect(containerWidth).toBeGreaterThan(1000);
  expect(sidebarWidth).toBe(280);
  expect(cardWidth).toBeGreaterThan(600);
});
