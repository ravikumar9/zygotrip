const { test, expect } = require('@playwright/test');

test('debug dropdown mechanism', async ({ page }) => {
  // Login as customer
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', 'customer@test.com');
  await page.fill('input[name="password"]', 'Test@123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/');
  
  // Wait for page to fully load
  await page.waitForTimeout(1000);
  
  // Check if dropdown exists
  const dropdown = await page.locator('.dropdown').count();
  console.log('Dropdown count:', dropdown);
  
  // Check if trigger exists
  const trigger = await page.locator('.dropdown-trigger').count();
  console.log('Trigger count:', trigger);
  
  // Check if menu exists
  const menu = await page.locator('.dropdown-menu').count();
  console.log('Menu count:', menu);
  
  // Log HTML structure
  const html = await page.locator('.dropdown').innerHTML();
  console.log('Dropdown HTML:', html);
  
  // Try to click trigger
  await page.locator('.dropdown-trigger').click();
  
  // Wait a bit  
  await page.waitForTimeout(500);
  
  // Check if active class was added
  const hasActive = await page.locator('.dropdown.active').count();
  console.log('Active dropdowns after click:', hasActive);
  
  // Check if menu is now visible
  const isVisible = await page.locator('.dropdown-menu').isVisible();
  console.log('Menu visible:', isVisible);
  
  // Check computed style
  const opacity = await page.locator('.dropdown-menu').evaluate(el => window.getComputedStyle(el).opacity);
  console.log('Menu opacity:', opacity);
  
  const visibility = await page.locator('.dropdown-menu').evaluate(el => window.getComputedStyle(el).visibility);
  console.log('Menu visibility CSS:', visibility);
});
