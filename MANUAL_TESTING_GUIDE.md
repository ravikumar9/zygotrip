# TEST CREDENTIALS FOR MANUAL VERIFICATION
# Generated: Feb 25, 2026

## USER ACCOUNTS FOR TESTING

### 1. TRAVELER ACCOUNT
- Email: traveler@example.com
- Password: Test@123456
- Role: Traveler
- Use Case: Browse properties, search, make bookings

### 2. PROPERTY OWNER ACCOUNT
- Email: owner@example.com
- Password: Owner@123456
- Role: Property Owner
- Use Case: Manage properties, set prices, view bookings
- Permissions: base_price, room_amenities, photos, inventory, discount

### 3. ADMIN ACCOUNT
- Email: admin@example.com
- Password: Admin@123456
- Role: System Administrator
- Use Case: Manage platform settings, fees, featured properties
- Permissions: platform_fee, service_fee, GST, featured status

---

## TEST DATA IN DATABASE

### Properties
- Count: 75 properties seeded
- Examples:
  - bangalore-grand-stay-1-blr (Bangalore, 4-star)
  - test-grand-hotel (Coorg, 4-star) 
  - coorg-homestay-1-cg (Coorg, Homestay)

### Dates for Testing
- Default Checkin: 2026-02-26 (tomorrow)
- Default Checkout: 2026-02-28 (in 2 days)
- Rooms: 1, Adults: 2, Children: 0 (standard search)

### Room Types
- Each property has 2-5 room types
- Examples: Deluxe Room, Basic Room, Suite, Budget Room
- Prices: ₹2,000 - ₹10,000 per night

---

## ROUTE TESTING CHECKLIST

### ✅ WORKING ROUTES
```
GET /hotels/
  Expected: Landing page with search form
  Status: 200 OK
  Has Form: Yes
  Redirects: 0

GET /hotels/search/?location=coorg&checkin=2026-02-26&...
  Expected: Search results with filters
  Status: 200 OK
  Has Filters: Yes (needs verification of dynamic counts)
  Redirects: 1 (unnecessary, should be 0)

GET /hotels/<slug>/?checkin=2026-02-26&checkout=2026-02-28&...
  Expected: Property detail page with room selection
  Status: 200 OK
  Has Room Selection: Needs verification
  Redirects: 0
```

### ❌ BROKEN ROUTES
```
GET /hotels/<slug>/booking/?room_type=1&checkin=...
  Expected: Booking page with guest form
  Status: 500 ERROR (exception in view)
  Issue: Unknown - needs server log analysis
```

---

## MANUAL TESTING STEPS

### 1. Test Landing Page
1. Go to https://127.0.0.1:8000/hotels/
2. Verify: Hero section visible, search form has these fields:
   - Location (text input or dropdown)
   - Check-in Date (date picker defaulting to tomorrow)
   - Check-out Date (date picker defaulting to day-after-tomorrow)
   - Number of Rooms (dropdown or spinner, default 1)
   - Adults (dropdown or spinner, default 2)
   - Children (dropdown or spinner, default 0)
3. Click "Search" button
4. Verify: Goes to /hotels/search/?... with canonical params

### 2. Test Search Results
1. On search page, verify:
   - Hotel cards display with name, image, rating
   - Filters visible on left side:
     [ ] Star Rating (1-5 stars with counts)
     [ ] Guest Rating (4.5+, 4.0+, 3.0+ with counts)
     [ ] Price Range (₹0-1K, ₹1K-2.5K, etc. with counts)
     [ ] Property Type (Hotel, Resort, Homestay, etc. with counts)
     [ ] Room Amenities (WiFi, AC, Pool, etc. with counts)
     [ ] Payment Mode (Pay at property, Card, etc.)
     [ ] Features (Free Cancellation, Breakfast, etc.)
   - Sort buttons: Popular, Price Low-High, Price High-Low, Rating, Newest
   - Page pagination (if >20 results)
2. Test Filter: Click "4 Star" filter
   - Verify: URL updates with &star=4
   - Verify: Results update to show only 4-star hotels
   - Verify: Filter count stays visible
3. Test Sort: Click "Price Low-High"
   - Verify: URL updates with &sort=price_low
   - Verify: Results reorder by price
   - Verify: Filters NOT reset, all still visible
4. Test Pagination: Click page 2 (if available)
   - Verify: URL updates with &page=2
   - Verify: Different hotels shown

### 3. Test Property Detail
1. Click on any hotel card
2. Property detail page should show:
   - Hotel name, rating, address
   - Photos with lazy loading (check browser DevTools)
   - Room type cards with:
     - Room name (e.g., "Deluxe Room")
     - Room-specific amenities (NOT property amenities)
     - Base price per night
     - Occupancy limit (e.g., "Max 2")
     - Cancellation policy
   - Guest summary at top showing: 2026-02-26 → 2026-02-28, 1 Room, 2 Adults
3. Click on a room type
   - Verify: Goes to booking page (or shows booking form)

### 4. Test Booking Page
1. Booking page should show:
   - Property name and star rating
   - Selected room type name and amenities
   - Dates: Check-in (2026-02-26) and Checkout (2026-02-28)
   - Guest count: 1 Room, 2 Adults
   - Price breakdown:
     - Base Price: ₹X per night × nights
     - Property Discount: -₹X (if applicable)
     - Subtotal: ₹X
     - Service Fee: ₹X
     - GST: ₹X
     - **Final Total: ₹X** (bold/highlighted)
   - Coupon field: Optional coupon code input
     - If coupon available: Auto-show "Apply STAYSAVER" or similar
     - After apply: Show "Coupon: STAYSAVER applied, Discount: ₹X"
   - Guest details form:
     - Email (pre-filled if logged in)
     - Name
     - Phone
     - Special requests (optional)
"Button: "Proceed to Payment" or "Confirm Booking"2. Fill form and click button
   - Verify: Redirects to payment page (/payments/checkout/)

### 5. Test Autosuggest
1. Go back to /hotels/
2. Click location field and type "coo"
3. Dropdown should show:
   - Cities: "Coorg (45 properties)"
   - Areas: "Madikeri (12 properties)"
   - Properties: "Coorg Grand Stay", "Coorg Homestay", etc.
4. Click "Coorg" (city)
   - Verify: Search goes to /hotels/search/?searchText=Coorg&cityCode=...

### 6. Test Reviews Display
1. On search results or detail page
2. Hotel cards should show rating like:
   - "4★ Hotel" or "🏨 4★"
   - "4.3 Excellent (109 reviews)"
3. On detail page, reviews should show:
   - Large rating: "4.3"
   - Label: "Excellent"
   - Count: "109 reviews, 85 verified"

### 7. Test Images
1. On search results page
2. Hotel images should:
   - Load immediately (lazy loading attribute set but image visible)
   - Show fallback placeholder if missing
   - Display properly on slow network (responsive srcset)
3. On detail page
   - Room images should be room-specific photos
   - If no room photos, should fallback to property photos
   - If no property photos, should show placeholder

---

## EXPECTED FILTER COUNTS (for verification)

When searching for "coorg" with dates 2026-02-26→2026-02-28:
- Star 5: ~5 properties
- Star 4: ~15 properties
- Star 3: ~10 properties
- 4.5+ rated: ~12 properties
- Price 2000-5000: ~25 properties
- Hotel type: ~20 properties
- WiFi amenity: ~30 properties
- (All counts should be dynamic - changeable based on filters applied)

---

## IF YOU FIND ISSUES

1. **Landing page doesn't show form**
   - Check: `templates/hotels/landing.html` exists
   - Check: Form has correct field names
   - Fix: Re-render landing template with form fields

2. **Filters don't show counts**
   - Check: `FilterService.get_all_filters()` being called in view
   - Check: Template iterates over filters and displays counts
   - Fix: Wire FilterService to view context

3. **Filters don't update results**
   - Check: URL updates when filter clicked
   - Check: View re-queries database with filter applied
   - Check: Template reflects filtered results
   - Fix: Ensure view applies filter chain

4. **Sorting disappears after filter**
   - Check: `sort` parameter persisted in URL
   - Check: ORM `.order_by()` applied after filters
   - Fix: Ensure sort in canonical params order

5. **Images showing broken**
   - Check: MEDIA_URL properly configured in urls.py
   - Check: Image paths in database are correct
   - Check: ImageHandler.validate_image_url() returns valid URLs
   - Fix: Check media URL routing

6. **Booking page returns 404/500**
   - Check: `hotel_booking` view exists in views/__init__.py
   - Check: URL pattern defined in urls.py
   - Check: Route matches pattern (not slug conflict)
   - Check: View parameters match URL capture groups
   - Fix: Add error handling and detailed logging

7. **Autosuggest returns no results**
   - Check: AutosuggestService.get_suggestions() being called
   - Check: Database has properties with matching names/locations
   - Check: API endpoint returns JSON
   - Fix: Wire AutosuggestService to API view

---

## NEXT STEPS IF YOU CAN'T PROCEED

If you can't fix issues:
1. Share server error logs (from Django stderr)
2. Share browser console errors (F12 DevTools)
3. Share specific URL that's broken
4. Share screenshot of the issue
5. Agent will diagnose and provide targeted fixes

For now, test what works and report findings.
