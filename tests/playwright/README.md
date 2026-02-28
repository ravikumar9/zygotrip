# Playwright E2E Test Suite

## Setup

1. **Install Playwright:**
   ```bash
   pip install playwright pytest-playwright
   playwright install chromium
   ```

2. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

3. **Run tests:**
   ```bash
   # Run all tests
   pytest tests/playwright/ --headed

   # Run specific test
   pytest tests/playwright/test_booking_funnel.py::TestBookingFunnel::test_01_hotel_listing_page_loads --headed

   # Run in headless mode (CI)
   pytest tests/playwright/

   # Generate HTML report
   pytest tests/playwright/ --html=reports/playwright_report.html
   ```

## Test Coverage

### Critical User Flows
1. ✅ Hotel listing page loads with search results
2. ✅ Filters work correctly (amenities, price, etc.)
3. ✅ Hotel details page loads with room options
4. ✅ Room-specific photos and amenities displayed
5. ✅ Property discounts show strike-through + badge
6. ✅ Select Room button navigates to booking page
7. ✅ Booking form validates required fields
8. ✅ Complete booking flow creates booking
9. ✅ Mobile responsive design works
10. ✅ Amenity filter counts remain accurate

## Screenshots

All tests generate screenshots in `screenshots/` folder:
- `01_listing_page.png` - Hotel search results
- `02_filters_applied.png` - Filters in action
- `03_hotel_details.png` - Hotel details page
- `04_room_details.png` - Room-specific information
- `05_discount_displayed.png` - Discount badges and pricing
- `06_select_room.png` - Booking page navigation
- `07_form_validation.png` - Form validation messages
- `08_booking_complete.png` - Booking confirmation
- `09_mobile_view.png` - Mobile responsive layout
- `10_filter_count_accuracy.png` - Filter count verification

## CI/CD Integration

Add to GitHub Actions workflow:
```yaml
- name: Run Playwright Tests
  run: |
    pip install playwright pytest-playwright
    playwright install --with-deps chromium
    python manage.py runserver &
    sleep 5
    pytest tests/playwright/ --video=retain-on-failure
```

## Debugging

Run with debug mode:
```bash
PWDEBUG=1 pytest tests/playwright/test_booking_funnel.py::TestBookingFunnel::test_01_hotel_listing_page_loads
```
