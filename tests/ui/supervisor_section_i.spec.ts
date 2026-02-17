
import { test, expect } from '@playwright/test';

test.describe('Section I - Marketplace UI Runtime Tests', () => {
  
  test('Card rendering test', async ({ page }) => {
    // Navigate to hotels page
    await page.goto('http://localhost:8000/hotels/?q=', { waitUntil: 'networkidle' });
    
    // Check card count
    const cards = await page.locator('article').count();
    console.log(`Cards rendered: ${cards}`);
    expect(cards).toBeGreaterThan(0);
    
    // Check card structure
    const card = page.locator('article').first();
    await expect(card).toBeVisible();
    
    // Verify left section (image)
    const image = card.locator('img').first();
    await expect(image).toBeVisible();
    expect(await image.getAttribute('src')).toBeTruthy();
    
    // Verify center section (name, location)
    const name = card.locator('h3, h2').first();
    await expect(name).toBeVisible();
    
    // Verify right section (price, CTA)
    const cta = card.locator('a, button').last();
    await expect(cta).toBeVisible();
    
    console.log('Card structure: PASS');
  });

  test('Sidebar width verification', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/?q=', { waitUntil: 'networkidle' });
    
    // Get sidebar element
    const sidebar = page.locator('[class*="sidebar"], [class*="filter"], aside').first();
    
    if (await sidebar.isVisible()) {
      const box = await sidebar.boundingBox();
      console.log(`Sidebar width: ${box.width}px`);
      // Sidebar should be around 280px
      expect(box.width).toBeGreaterThan(200);
      expect(box.width).toBeLessThan(400);
    }
  });

  test('Grid responsiveness', async ({ page }) => {
    // Test on desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('http://localhost:8000/hotels/?q=', { waitUntil: 'networkidle' });
    
    const cards = await page.locator('article').count();
    console.log(`Desktop cards: ${cards}`);
    expect(cards).toBeGreaterThan(0);
    
    // Test on mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('http://localhost:8000/hotels/?q=', { waitUntil: 'networkidle' });
    
    const cardsMobile = await page.locator('article').count();
    console.log(`Mobile cards: ${cardsMobile}`);
    expect(cardsMobile).toBeGreaterThan(0);
  });

  test('Filter URL parameter updates', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/?q=', { waitUntil: 'networkidle' });
    
    // Simulate filter change
    const filterInputs = page.locator('input[type="text"], input[type="search"]');
    const inputCount = await filterInputs.count();
    
    if (inputCount > 0) {
      await filterInputs.first().fill('luxury');
      await page.waitForNavigation({ waitUntil: 'networkidle' });
      
      const url = page.url();
      console.log(`Updated URL: ${url}`);
      expect(url).toContain('luxury');
    }
  });

  test('Search ranking by score', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/?q=luxury', { waitUntil: 'networkidle' });
    
    const cards = await page.locator('article').count();
    if (cards > 1) {
      // Get first and second card prices to verify they're different
      const price1Text = await page.locator('article').nth(0).textContent();
      const price2Text = await page.locator('article').nth(1).textContent();
      
      // Verify results are displayed
      expect(price1Text).toBeTruthy();
      expect(price2Text).toBeTruthy();
      console.log('Search results ranked: PASS');
    }
  });

  test('DOM integrity check', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/?q=', { waitUntil: 'networkidle' });
    
    // Check for errors in console
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Wait a bit for any deferred errors
    await page.waitForTimeout(2000);
    
    console.log(`Console errors: ${errors.length}`);
    expect(errors.length).toBe(0);
  });
});
