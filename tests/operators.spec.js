const { test, expect } = require('@playwright/test');

async function login(page, email, password = 'Test@123') {
  await page.goto('/accounts/login/');
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL(/\/|dashboard/);
}

// ==========================================
// BUS OPERATOR DASHBOARD TESTS
// ==========================================

test('bus_operator: dashboard displays buses', async ({ page }) => {
  await login(page, 'bus_operator_1@test.com');
  await page.goto('/buses/dashboard/');
  
  // Verify dashboard loads
  await expect(page.getByText(/Bus Fleet Dashboard|bus_operator_1/i)).toBeVisible();
  await expect(page.getByRole('heading', { name: /Buses|Fleet/i })).toBeVisible();
});

test('bus_operator: can create new bus', async ({ page }) => {
  await login(page, 'bus_operator_1@test.com');
  await page.goto('/buses/dashboard/');
  
  // Click create bus button
  await page.getByRole('button', { name: /Add Bus|Create Bus|New Bus/i }).click();
  await page.waitForURL(/\/buses\/create/);
  
  // Fill form
  await page.fill('input[name="bus_number"]', 'TST-001');
  await page.selectOption('select[name="bus_type"]', { index: 0 });
  await page.fill('input[name="total_seats"]', '50');
  await page.fill('input[name="route"]', 'Delhi to Mumbai');
  
  // Submit form
  await page.getByRole('button', { name: /Create|Save|Submit/i }).click();
  await page.waitForURL(/\/buses\/dashboard\/|\/buses\/\d+/);
  
  // Verify success
  await expect(page.getByText(/success|created|created bus|Bus created/i)).toBeVisible();
});

test('bus_operator: can update bus availability', async ({ page }) => {
  await login(page, 'bus_operator_1@test.com');
  await page.goto('/buses/dashboard/');
  
  // Find first bus and click detail
  const busCard = page.locator('[class*="bus"]:has-text("KT-")').first();
  if (await busCard.isVisible()) {
    await busCard.click();
    await page.waitForURL(/\/buses\/\d+/);
    
    // Toggle availability (atomic operation)
    const availabilityToggle = page.getByRole('button', { name: /toggleAvailability|availability|Toggle/i });
    if (await availabilityToggle.isVisible()) {
      const initialState = await availabilityToggle.getAttribute('data-available');
      await availabilityToggle.click();
      await page.waitForTimeout(500); // Wait for atomic update
      
      const newState = await availabilityToggle.getAttribute('data-available');
      expect(newState).not.toBe(initialState);
    }
  }
});

test('bus_operator: can view bookings', async ({ page }) => {
  await login(page, 'bus_operator_1@test.com');
  await page.goto('/buses/dashboard/');
  
  // Navigate to bookings
  const bookingsLink = page.getByRole('link', { name: /Bookings|View Bookings/i });
  if (await bookingsLink.isVisible()) {
    await bookingsLink.click();
    await page.waitForURL(/\/buses\/bookings|\/bookings/);
    
    // Verify bookings page loads
    await expect(page.getByText(/Booking|Bookings/i)).toBeVisible();
  }
});

// ==========================================
// CAB OWNER DASHBOARD TESTS
// ==========================================

test('cab_owner: dashboard displays cabs', async ({ page }) => {
  await login(page, 'cab_owner_1@test.com');
  await page.goto('/cabs/dashboard/');
  
  // Verify dashboard loads
  await expect(page.getByText(/Cab Fleet Dashboard|cab_owner_1|Cabs/i)).toBeVisible();
  await expect(page.getByRole('heading', { name: /Cabs|Fleet/i })).toBeVisible();
});

test('cab_owner: can create new cab', async ({ page }) => {
  await login(page, 'cab_owner_1@test.com');
  await page.goto('/cabs/dashboard/');
  
  // Click create cab button
  await page.getByRole('button', { name: /Add Cab|Create Cab|New Cab/i }).click();
  await page.waitForURL(/\/cabs\/create/);
  
  // Fill form
  await page.fill('input[name="registration_number"]', 'DL-01-TEST-001');
  await page.selectOption('select[name="vehicle_type"]', { index: 0 });
  await page.fill('input[name="base_fare"]', '50');
  await page.fill('input[name="rate_per_km"]', '15');
  
  // Submit form
  await page.getByRole('button', { name: /Create|Save|Submit/i }).click();
  await page.waitForURL(/\/cabs\/dashboard\/|\/cabs\/\d+/);
  
  // Verify success
  await expect(page.getByText(/success|created|created cab|Cab created/i)).toBeVisible();
});

test('cab_owner: can update cab pricing', async ({ page }) => {
  await login(page, 'cab_owner_1@test.com');
  await page.goto('/cabs/dashboard/');
  
  // Find first cab
  const cabCard = page.locator('[class*="cab"]:has-text("₹")').first();
  if (await cabCard.isVisible()) {
    await cabCard.click();
    await page.waitForURL(/\/cabs\/\d+/);
    
    // Update pricing
    const updateBtn = page.getByRole('button', { name: /Update|Edit/i });
    if (await updateBtn.isVisible()) {
      await updateBtn.click();
      await page.fill('input[name="base_fare"]', '75');
      await page.fill('input[name="rate_per_km"]', '18');
      await page.getByRole('button', { name: /Save|Submit/i }).click();
      
      await expect(page.getByText(/success|updated/i)).toBeVisible();
    }
  }
});

test('cab_owner: can deactivate cab', async ({ page }) => {
  await login(page, 'cab_owner_1@test.com');
  await page.goto('/cabs/dashboard/');
  
  // Find a cab and deactivate
  const deactivateBtn = page.getByRole('button', { name: /Deactivate|Disable|Remove/i }).first();
  if (await deactivateBtn.isVisible()) {
    await deactivateBtn.click();
    await page.waitForTimeout(500);
    
    // Verify deactivation
    await expect(page.getByText(/deactivated|disabled/i)).toBeVisible();
  }
});

// ==========================================
// PACKAGE PROVIDER DASHBOARD TESTS
// ==========================================

test('package_provider: dashboard displays packages', async ({ page }) => {
  await login(page, 'package_provider_1@test.com');
  await page.goto('/packages/dashboard/');
  
  // Verify dashboard loads
  await expect(page.getByText(/Package Dashboard|package_provider_1|Packages/i)).toBeVisible();
  await expect(page.getByRole('heading', { name: /Packages|Tours/i })).toBeVisible();
});

test('package_provider: can create new package', async ({ page }) => {
  await login(page, 'package_provider_1@test.com');
  await page.goto('/packages/dashboard/');
  
  // Click create package button
  await page.getByRole('button', { name: /Add Package|Create Package|New Package/i }).click();
  await page.waitForURL(/\/packages\/create/);
  
  // Fill form
  await page.fill('input[name="name"]', 'Alpine Adventure');
  await page.fill('textarea[name="description"]', 'Explore snow-capped mountains');
  await page.fill('input[name="duration_days"]', '7');
  await page.fill('input[name="price"]', '45000');
  await page.selectOption('select[name="difficulty_level"]', { index: 0 });
  
  // Submit form
  await page.getByRole('button', { name: /Create|Save|Submit/i }).click();
  await page.waitForURL(/\/packages\/dashboard\/|\/packages\/\d+/);
  
  // Verify success
  await expect(page.getByText(/success|created|created package|Package created/i)).toBeVisible();
});

test('package_provider: can update package pricing', async ({ page }) => {
  await login(page, 'package_provider_1@test.com');
  await page.goto('/packages/dashboard/');
  
  // Find first package
  const packageCard = page.locator('[class*="package"]:has-text("₹")').first();
  if (await packageCard.isVisible()) {
    await packageCard.click();
    await page.waitForURL(/\/packages\/\d+/);
    
    // Update pricing
    const updatePriceBtn = page.getByRole('button', { name: /Update Price|Edit Price/i });
    if (await updatePriceBtn.isVisible()) {
      await updatePriceBtn.click();
      await page.fill('input[name="price"]', '55000');
      await page.getByRole('button', { name: /Save|Update/i }).click();
      
      await expect(page.getByText(/success|updated/i)).toBeVisible();
    }
  }
});

test('package_provider: can toggle package active status', async ({ page }) => {
  await login(page, 'package_provider_1@test.com');
  await page.goto('/packages/dashboard/');
  
  // Find package and toggle active status
  const toggleBtn = page.getByRole('button', { name: /Activate|Deactivate|Toggle/i }).first();
  if (await toggleBtn.isVisible()) {
    const initialState = await toggleBtn.getAttribute('data-active');
    await toggleBtn.click();
    await page.waitForTimeout(500);
    
    const newState = await toggleBtn.getAttribute('data-active');
    expect(newState).not.toBe(initialState);
  }
});
