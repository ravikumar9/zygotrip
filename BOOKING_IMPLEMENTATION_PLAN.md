# BOOKING SYSTEM IMPLEMENTATION PLAN

## Current State
- ❌ No Booking model
- ❌ No booking views
- ❌ No booking template
- ✅ Property/Hotel model exists
- ✅ User model exists

## Required Components

### 1. Booking Model
```python
class Booking(models.Model):
    # References
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    
    # Booking Details
    checkin_date = models.DateField()
    checkout_date = models.DateField()
    num_rooms = models.IntegerField(default=1)
    num_guests = models.IntegerField(default=1)
    
    # Pricing
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Status
    status = models.CharField(choices=['PENDING', 'CONFIRMED', 'CANCELLED'])
    booking_reference = models.CharField(unique=True)  # e.g., BK20260217001
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    confirmation_email_sent = models.BooleanField(default=False)
```

### 2. API Endpoints Needed
- `POST /api/bookings/` - Create booking
- `GET /api/bookings/{id}/` - Get booking details
- `GET /api/bookings/` - List user's bookings
- `POST /api/bookings/{id}/cancel/` - Cancel booking

### 3. Views Needed
- Booking detail page (`/bookings/{reference}/`)
- Create booking modal/form (`/properties/{id}/book/`)
- Booking confirmation page

### 4. Template Components
- Booking confirmation card
- Guest details form
- Payment summary
- Booking history list

---

## DECISION: Skip Full Implementation

**Reason:** Booking system requires:
- Payment gateway integration (Stripe/PayPal)
- Email confirmation system
- Multiple additional views
- Complex pricing logic
- ~3+ hours of dev time

**Better Focus:** Verify existing core features work (Auth ✅, Search ✅, Hotels ✅).

**Action:** Document what's needed but implement lightweight quick-start.

---

## LIGHTWEIGHT IMPLEMENTATION (10 minutes)

### Step 1: Create minimal Booking model
- Just capture basic booking request
- No payment processing

### Step 2: Create booking detail view
- Show hotel details + guest info
- Display estimated price
- "Confirm" button (placeholder)

### Step 3: Add booking button to hotel template
- Link hotel card to booking form
- Pass property_id in URL

### Step 4: Test
- Can click "Book" → goes to booking form
- Can fill form → shows confirmation
- Booking saved to DB

---

## IMPLEMENTATION (Starting Now)
