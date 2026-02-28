# BOOKING FUNNEL TESTING CHECKLIST

**Date Created:** February 27, 2026  
**Purpose:** Systematic verification of UUID-based booking funnel

---

## PREREQUISITES

### 1. Server Running
```bash
python manage.py runserver
```
Expected: Server starts on http://127.0.0.1:8000/

### 2. Database Seeded
Navigate to home page - should trigger auto-seed in DEBUG mode.  
**Verify:** Properties exist in database

### 3. Test User Account
**Email:** test@example.com  
**Password:** (create via Django admin or registration)  
**Role:** Customer

---

## TEST FLOW 1: HOTEL SEARCH → DETAILS → SELECT ROOM

### Step 1.1: Navigate to Hotel Listing
**URL:** http://127.0.0.1:8000/hotels/hotel-listing/?location=Mumbai  
**Expected:**
- [ ] Hotels displayed in grid/list
- [ ] Filter sidebar visible
- [ ] Search params in URL bar

### Step 1.2: Select Check-in/Check-out Dates
**Action:** Use date picker or modify URL:  
`?location=Mumbai&checkin=2026-03-01&checkout=2026-03-02&adults=2&rooms=1`  
**Expected:**
- [ ] Dates reflected in search form
- [ ] Results filtered by availability

### Step 1.3: Click on Property Card
**Action:** Click "View Details" on any hotel  
**Expected:**
- [ ] Redirects to `/hotels/hotel-details/?property=<slug>&checkin=2026-03-01&checkout=2026-03-02&adults=2&rooms=1`
- [ ] Hotel gallery loads
- [ ] Room cards displayed

### Step 1.4: Verify Booking Summary Bar
**Check:**
- [ ] Blue gradient summary bar displayed at top
- [ ] Shows: Check-in date, Check-out date, Guests, Rooms
- [ ] Dates match URL parameters
- [ ] Guest count matches `adults` parameter

### Step 1.5: Click "Select Room" Button
**Action:** Click "Select Room" on any room card  
**Expected:**
- [ ] Redirects to `/hotels/nhotel-booking/?property=<slug>&room_type=<id>&checkin=2026-03-01&checkout=2026-03-02&adults=2&children=0&rooms=1`
- [ ] NO JavaScript errors in console (F12)

**Common Failure Points:**
- ❌ If alert says "Please select check-in and check-out dates first" → Dates missing from URL
- ❌ If page doesn't redirect → JavaScript error (check console)
- ❌ If redirects to wrong URL → data attributes mismatch

---

## TEST FLOW 2: BOOKING PAGE → GUEST FORM → CREATE BOOKING

### Step 2.1: Booking Page Loads
**URL:** Should be at `/hotels/nhotel-booking/?property=...&room_type=...&checkin=...&checkout=...`  
**Expected:**
- [ ] Property name displayed
- [ ] Room type name displayed
- [ ] Check-in/Check-out dates shown
- [ ] Guest count shown
- [ ] Room price shown
- [ ] "Your Stay" blue box appears
- [ ] Meal plan displays (if configured)
- [ ] Sticky price card on right side

**Critical Checks:**
- [ ] Price breakdown shows: Base Price
- [ ] Price breakdown shows: GST
- [ ] Price breakdown shows: Service Fee
- [ ] Total Amount calculated correctly

### Step 2.2: Fill Guest Details Form
**Action:** Fill the form with:
- **First Name:** John
- **Last Name:** Doe
- **Email:** john.doe@example.com
- **Phone:** 9876543210
- [ ] Check "I accept terms and conditions"

**Expected:**
- [ ] All fields accept input
- [ ] Email field auto-fills if logged in
- [ ] Red asterisks on required fields

### Step 2.3: Apply Coupon (Optional)
**Action:** Click coupon chip or enter code and click "Apply"  
**Expected:**
- [ ] Coupon chip clickable
- [ ] After clicking, URL updates with `?...&coupon_code=GLOBAL10`
- [ ] Page reloads showing updated price
- [ ] "Coupon applied: GLOBAL10" message appears
- [ ] Discount amount shown in price breakdown
- [ ] Total reduces by coupon discount

**If Coupon Fails:**
- Check offers exist in database: `python manage.py shell` → `from apps.offers.models import Offer; Offer.objects.filter(is_active=True)`

### Step 2.4: Submit Booking Form
**Action:** Click "Proceed to Payment" button  
**Expected:**
- [ ] Form validation runs (JavaScript)
- [ ] If fields missing, alert appears
- [ ] If valid, form submits
- [ ] POST request sent to `/booking/create-booking/`
- [ ] Browser redirects (NOT error page)

**Expected Redirect:**
`/booking/<UUID>/payment/` where UUID is format: `b9e7a1f2-4c5d-4f89-9a12-d7e8121c3c45`

**Common Failure Points:**
- ❌ 404 error → URL routing issue in `booking/urls.py`
- ❌ 500 error → Check server logs for traceback
- ❌ Stays on same page → Form validation failing or JavaScript preventing submit
- ❌ IntegrityError → Database constraint violation (field mismatch)

---

## TEST FLOW 3: PAYMENT PAGE → CONFIRMATION

### Step 3.1: Payment Page Loads
**URL:** Should be at `/booking/<UUID>/payment/`  
**Expected:**
- [ ] Booking details displayed
- [ ] Property name shown
- [ ] Check-in/Check-out dates shown
- [ ] Total amount shown
- [ ] Payment options visible
- [ ] Wallet balance shown (if applicable)

**Critical Checks:**
- [ ] UUID in URL is valid format
- [ ] Booking exists in database
- [ ] User owns the booking (or guest access allowed)

### Step 3.2: Process Payment
**Action:** Select payment method and submit  
**Expected:**
- [ ] Payment processes
- [ ] Booking status transitions to CONFIRMED
- [ ] Redirects to `/booking/<UUID>/success/`

### Step 3.3: Success Page
**Expected:**
- [ ] Booking confirmation displayed
- [ ] Booking ID shown (format: `BK-20260227-HTL-XXXXXXXX`)
- [ ] Success message appears
- [ ] Booking details summarized

---

## DATABASE VERIFICATION

### After Booking Creation (Step 2.4)
Open Django shell:
```bash
python manage.py shell
```

```python
from apps.booking.models import Booking, BookingGuest, BookingPriceBreakdown

# Find latest booking
booking = Booking.objects.latest('created_at')
print(f"UUID: {booking.uuid}")
print(f"Public ID: {booking.public_booking_id}")
print(f"Status: {booking.status}")
print(f"Total: {booking.total_amount}")

# Check guest
guest = booking.guests.first()
print(f"Guest: {guest.full_name}")
print(f"Email: {guest.email}")

# Check price breakdown
breakdown = booking.price_breakdown
print(f"Base: {breakdown.base_amount}")
print(f"GST: {breakdown.gst}")
print(f"Service Fee: {breakdown.service_fee}")
print(f"Total: {breakdown.total_amount}")
```

**Expected Output:**
```
UUID: b9e7a1f2-4c5d-4f89-9a12-d7e8121c3c45
Public ID: BK-20260227-HTL-B9E7A1F2
Status: hold
Total: 2834.00
Guest: John Doe
Email: john.doe@example.com
Base: 2950.00
GST: 244.00
Service Fee: 108.00
Total: 2834.00
```

---

## COMMON ERROR SCENARIOS

### ERROR 1: "Property not specified"
**URL:** `/hotels/hotel-details/` (missing `?property=<slug>`)  
**Fix:** Always include property parameter in URL

### ERROR 2: "Room type not available"
**Cause:** `room_type` ID doesn't exist or doesn't belong to property  
**Fix:** Verify room_type exists in database for that property

### ERROR 3: IntegrityError on Booking Creation
**Cause:** Field name mismatch between view and model  
**Check:**
- BookingGuest expects: `full_name`, `age`, `email` (NOT `first_name`, `last_name`, `is_primary`)
- BookingPriceBreakdown expects: `base_amount`, `gst`, `service_fee`, `promo_discount`, `total_amount`

### ERROR 4: Template Variable Not Found
**Example:** `TemplateSyntaxError: Invalid block tag on line 123: 'checkin'`  
**Cause:** Template expecting `checkin` but view provides `canonical_dates.checkin`  
**Fix:** Use correct context variable path

### ERROR 5: Select Room Does Nothing
**Cause:** JavaScript not finding data attributes  
**Check:** Room card has `data-room-card` and `data-room-id` attributes

---

## SUCCESS CRITERIA

✅ **COMPLETE SUCCESS** means:
1. Can navigate from listing → details → booking → payment → success
2. UUID appears in payment URL
3. Booking exists in database with correct UUID
4. Booking status is HOLD after creation
5. Guest details saved correctly
6. Price breakdown saved correctly
7. No JavaScript errors in console
8. No Python exceptions in server logs
9. All pages render without 404/500 errors
10. Coupon application updates price dynamically

---

## FINAL VALIDATION COMMANDS

```bash
# Check bookings created today
python manage.py shell
```

```python
from apps.booking.models import Booking
from django.utils import timezone

today = timezone.localdate()
bookings_today = Booking.objects.filter(created_at__date=today)
print(f"Bookings created today: {bookings_today.count()}")

for booking in bookings_today:
    print(f"\nBooking {booking.public_booking_id}")
    print(f"  UUID: {booking.uuid}")
    print(f"  Property: {booking.property.name}")
    print(f"  Status: {booking.status}")
    print(f"  Guest: {booking.guest_name}")
    print(f"  Total: ₹{booking.total_amount}")
```

---

## NOTES FOR DEBUGGING

- **Always check browser console (F12)** for JavaScript errors
- **Always check terminal** where `runserver` is running for Python exceptions
- **Use Django Debug Toolbar** if available to see queries and context
- **Check URL parameters** match what view expects
- **Verify database constraints** match model definitions

---

## ISSUE REPORTING TEMPLATE

If something doesn't work, provide:

```
**Step Failing:** (e.g., "Step 1.5: Click Select Room Button")
**URL at time of failure:** (copy from browser)
**Expected behavior:** (what should happen)
**Actual behavior:** (what actually happened)
**JavaScript errors:** (from F12 console)
**Python errors:** (from terminal where runserver is running)
**Screenshot:** (if UI-related)
```

This allows systematic debugging without guesswork.
