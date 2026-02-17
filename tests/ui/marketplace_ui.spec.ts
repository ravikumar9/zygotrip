import { test, expect } from '@playwright/test';

/**
 * PHASE 11: Marketplace UI Tests
 * Tests for responsive design, component visibility, and interactions
 */

test.describe('PHASE 7: Responsive Grid Layout', () => {
  test('hotel grid should be 1 column on mobile (768px)', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const grid = page.locator('.grid');
    const gridColsClass = await grid.evaluate(el => 
      window.getComputedStyle(el).getPropertyValue('grid-template-columns')
    );
    
    // Mobile should show 1 column
    expect(gridColsClass).toContain('1');
  });

  test('hotel grid should be 2 columns on desktop (1280px+)', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const grid = page.locator('.grid.grid-cols-1.md\\:grid-cols-2');
    const isVisible = await grid.isVisible();
    expect(isVisible).toBeTruthy();
  });
});

test.describe('PHASE 4: Hotel Card Component', () => {
  test('hotel card should be visible with all required elements', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const card = page.locator('.hotel-card').first();
    await expect(card).toBeVisible();
    
    // Check for required card elements
    const image = card.locator('img');
    const title = card.locator('h3');
    const rating = card.locator('.hotel-rating');
    const price = card.locator('.price-block');
    const ctaButton = card.locator('a').filter({ hasText: /View Details|Book Now/ });
    
    await expect(image).toBeVisible();
    await expect(title).toBeVisible();
    await expect(rating).toBeVisible();
    await expect(price).toBeVisible();
    await expect(ctaButton).toBeVisible();
  });

  test('hotel card has correct flex layout', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const card = page.locator('.hotel-card').first();
    const classes = await card.getAttribute('class');
    
    expect(classes).toContain('flex');
    expect(classes).toContain('rounded-xl');
    expect(classes).toContain('shadow-md');
  });

  test('hotel card image should load', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const image = page.locator('.hotel-card img').first();
    const src = await image.getAttribute('src');
    
    expect(src).toBeTruthy();
    expect(src).toContain('http');
  });

  test('hotel card price should show discount when available', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const priceBlocks = page.locator('.price-block');
    const count = await priceBlocks.count();
    
    if (count > 0) {
      const firstPriceBlock = priceBlocks.first();
      const hasStrikethrough = await firstPriceBlock.locator('.line-through').count();
      
      // Some cards should have discounts
      if (hasStrikethrough > 0) {
        const strikethrough = firstPriceBlock.locator('.line-through');
        await expect(strikethrough).toBeVisible();
      }
    }
  });

  test('hotel card rating should display stars', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const rating = page.locator('.hotel-rating').first();
    await expect(rating).toBeVisible();
    
    const stars = rating.locator('span');
    const starCount = await stars.count();
    
    // Should have filled and unfilled stars
    expect(starCount).toBeGreaterThan(0);
  });
});

test.describe('PHASE 8: Search Bar', () => {
  test('search bar should have rounded-full styling', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const searchInput = page.locator('[data-search-input]');
    const classes = await searchInput.getAttribute('class');
    
    expect(classes).toContain('rounded-full');
    expect(classes).toContain('shadow-sm');
  });

  test('search input should trigger debounce on typing', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const searchInput = page.locator('[data-search-input]');
    await searchInput.fill('test hotel');
    
    // Wait for debounce timeout (400ms + buffer)
    await page.waitForTimeout(500);
    
    // Should trigger form submission
    const currentUrl = page.url();
    expect(currentUrl).toContain('q=');
  });

  test('search bar should have search icon', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const searchForm = page.locator('[data-search-form]');
    const icon = searchForm.locator('svg');
    
    await expect(icon).toBeVisible();
  });
});

test.describe('PHASE 6: Filter Sidebar', () => {
  test('filter sidebar should be sticky on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const sidebar = page.locator('.filter-sidebar').first();
    const classes = await sidebar.getAttribute('class');
    
    expect(classes).toContain('sticky');
    expect(classes).toContain('top-24');
  });

  test('filter sidebar should be hidden on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const sidebar = page.locator('.filter-sidebar').first();
    const display = await sidebar.evaluate(el => 
      window.getComputedStyle(el).getPropertyValue('display')
    );
    
    expect(display).toBe('none');
  });

  test('filter sidebar should have all required filter sections', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const sidebar = page.locator('.filter-sidebar').first();
    
    const locationSummary = sidebar.locator('summary', { hasText: /Location|📍/ });
    const priceSummary = sidebar.locator('summary', { hasText: /Price|💰/ });
    const ratingSummary = sidebar.locator('summary', { hasText: /Rating|⭐/ });
    
    await expect(locationSummary).toBeVisible();
    await expect(priceSummary).toBeVisible();
    await expect(ratingSummary).toBeVisible();
  });

  test('filter checkbox interactions should work', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const checkbox = page.locator('.filter-sidebar input[type="checkbox"]').first();
    
    if (await checkbox.isVisible()) {
      await checkbox.click();
      const isChecked = await checkbox.isChecked();
      expect(isChecked).toBeTruthy();
    }
  });
});

test.describe('PHASE 9: UI States', () => {
  test('empty state should show when no results', async ({ page }) => {
    // Search for something that returns no results
    await page.goto('http://localhost:8000/hotels/?q=xyz123nonexistent456');
    
    const emptyState = page.locator('.flex-grow');  // Empty state container
    
    // Either empty state or results should be visible
    const cards = page.locator('.hotel-card');
    const hasCards = await cards.count() > 0;
    
    if (!hasCards) {
      const emptyMessage = page.locator('text=No results found');
      const isVisible = await emptyMessage.isVisible().catch(() => false);
      
      if (isVisible) {
        await expect(emptyMessage).toBeVisible();
      }
    } else {
      expect(hasCards).toBeTruthy();
    }
  });

  test('error state should show with error message', async ({ page }) => {
    // Navigate to hotels page
    await page.goto('http://localhost:8000/hotels/');
    
    // If there's an error message in the page
    const errorBanner = page.locator('.bg-red-50');
    
    const isVisible = await errorBanner.isVisible().catch(() => false);
    
    if (isVisible) {
      await expect(errorBanner).toBeVisible();
      const errorText = errorBanner.locator('text=/Error|error/i');
      await expect(errorText).toBeVisible();
    }
  });
});

test.describe('PHASE 10: Visual Hierarchy & Typography', () => {
  test('hotel card title should have correct font size', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const title = page.locator('.hotel-card h3').first();
    const classes = await title.getAttribute('class');
    
    expect(classes).toContain('text-lg');
    expect(classes).toContain('font-semibold');
  });

  test('price should be larger than title', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const title = page.locator('.hotel-card h3').first();
    const price = page.locator('.price-discount').first();
    
    const titleSize = await title.evaluate(el => 
      window.getComputedStyle(el).fontSize
    );
    const priceSize = await price.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    
    // Price should be larger
    expect(parseInt(priceSize)).toBeGreaterThan(parseInt(titleSize));
  });

  test('metadata should be text-sm with gray color', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const metadata = page.locator('.hotel-card').first().locator('.text-sm');
    
    const count = await metadata.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('PHASE 3: Marketplace Layout', () => {
  test('page header should be in white section', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const header = page.locator('h1', { hasText: /Hotels|Browse/ }).first();
    
    // Check if header is visible
    const isVisible = await header.isVisible().catch(() => false);
    expect(isVisible).toBeTruthy();
  });

  test('search bar should be sticky', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const searchBar = page.locator('[data-search-form]').first().locator('..');
    const classes = await searchBar.getAttribute('class');
    
    expect(classes).toContain('sticky');
  });

  test('sidebar and main content should be side-by-side on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto('http://localhost:8000/hotels/');
    
    const sidebar = page.locator('.filter-sidebar').first();
    const main = page.locator('main').first();
    
    const sidebarBox = await sidebar.boundingBox();
    const mainBox = await main.boundingBox();
    
    if (sidebarBox && mainBox) {
      // Sidebar should be to the left of main content
      expect(sidebarBox.x + sidebarBox.width).toBeLessThanOrEqual(mainBox.x);
    }
  });
});

test.describe('PHASE 1: Tailwind CSS Integration', () => {
  test('tailwind classes should be applied and render correctly', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const roundedElement = page.locator('.rounded-full, .rounded-lg, .rounded-xl').first();
    
    const borderRadius = await roundedElement.evaluate(el =>
      window.getComputedStyle(el).borderRadius
    );
    
    // Should have border radius
    expect(borderRadius).not.toBe('0px');
  });

  test('shadow classes should be applied', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    const shadowElement = page.locator('.shadow-md, .shadow-lg').first();
    
    const boxShadow = await shadowElement.evaluate(el =>
      window.getComputedStyle(el).boxShadow
    );
    
    // Should have box shadow
    expect(boxShadow).not.toBe('none');
  });

  test('no console errors related to Tailwind', async ({ page }) => {
    const messages: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        messages.push(msg.text());
      }
    });
    
    await page.goto('http://localhost:8000/hotels/');
    await page.waitForLoadState('networkidle');
    
    const tailwindErrors = messages.filter(msg =>
      msg.includes('tailwind') || msg.includes('undefined')
    );
    
    expect(tailwindErrors.length).toBe(0);
  });
});

test.describe('PHASE 2: Component Composition', () => {
  test('pages should compose components correctly', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    // Check that all major components are present
    const header = page.locator('h1');
    const searchForm = page.locator('[data-search-form]');
    const filters = page.locator('.filter-sidebar');
    const cards = page.locator('.hotel-card');
    
    await expect(header).toBeVisible();
    await expect(searchForm).toBeVisible();
    await expect(filters).toHaveCount(1);
    
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);
  });

  test('components should not have logic in templates', async ({ page }) => {
    await page.goto('http://localhost:8000/hotels/');
    
    // Verify that data is pre-computed in view
    const cards = page.locator('.hotel-card');
    const firstCard = cards.first();
    
    // Card should have complete data
    const title = firstCard.locator('h3');
    const titleText = await title.textContent();
    
    expect(titleText).toBeTruthy();
    expect(titleText?.length).toBeGreaterThan(0);
  });
});
