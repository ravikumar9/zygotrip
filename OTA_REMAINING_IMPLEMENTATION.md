"""
COMPREHENSIVE OTA IMPLEMENTATION PLAN
=====================================

This document outlines all remaining work based on the MASTER OTA DIRECTIVE.

## ✅ COMPLETED (Session Just Finished)

1. **Hotels Hyperlink**: Correctly routes to /hotels/ ✓
2. **Property-Locality Linkage**: 65 properties linked to localities ✓
   - Madikeri: 2 properties
   - Virajpet: 1 property
   - Other localities populated
3. **Autosuggest Enhancement**: Shows area-wise property counts ✓
   - "Madikeri, Coorg (2 properties)"
   - "Virajpet, Coorg (1 properties)"
4. **Landing Page Sections Added**: ✓
   - Recent Searches (user/session based)
   - Offers For You (from database)
   - Daily Deals (properties with active offers)
5. **Offers System**: Verified database-driven (not UI hacks) ✓
   - Global offers exist
   - Property-specific offers linked

## 🔴 CRITICAL PRIORITY (Next Session)

### 1. Hotel Details Page Rebuild
**Issues**:
- Images not loading consistently
- Meal plan not displayed
- Layout "dirty" per user feedback
- Need Goibibo-style structure

**Actions Required**:
```python
# A. Add meal_plan to RoomType model
# Migration: apps/rooms/migrations/0002_add_meal_plan.py
# Field: meal_plan = CharField(choices=[...], default='room_only')

# B. Fix room card to display meal plan
# Template: templates/hotels/components/room_card.html
# Add meal plan badge below room name

# C. Fix image loading in room cards
# Current: Uses image_url only
# Fix: Use image.url when available, fallback to image_url
# Pattern: {% if room_image.image %}{{ room_image.image.url }}{% else %}{{ room_image.image_url }}{% endif %}

# D. Add Google Maps integration
# Template: templates/hotels/detail.html
# Add "View on Map" button with property.latitude, property.longitude
# Link: https://www.google.com/maps?q=<lat>,<lng>

# E. Restructure detail page layout
# Reference Goibibo structure:
# - Hero image gallery (full width)
# - Property info (name, address, stars, rating)
# - Tabbed sections (Rooms, Amenities, Policies, Reviews, Location)
# - Sticky booking sidebar (dates, guests, price summary)
```

### 2. Booking Page Price Breakdown
**Issues**:
- Only shows final price
- No breakdown (base → discount → service fee → taxes)
- Coupon auto-suggestions missing
- Layout needs structure

**Actions Required**:
```python
# A. Update PriceEngine to return breakdown
# File: apps/pricing/price_engine.py
# Return dict with: base_price, property_discount, coupon_discount, service_fee, gst, total

# B. Update booking view to pass breakdown to template
# File: apps/hotels/views/__init__.py → hotel_booking()
# Calculate full breakdown and add to context

# C. Update booking template
# File: templates/hotels/booking.html
# Add Price Summary section with line items:
# - Base Price: ₹X
# - Property Discount: -₹Y
# - Coupon Discount (CODE): -₹Z
# - Service Fee: ₹A
# - GST (18%): ₹B
# - Total Amount: ₹FINAL

# D. Add coupon auto-suggestions
# Query active coupons applicable to property
# Display as clickable cards with discount preview
# Auto-apply best coupon by default
```

### 3. Admin Approval Settings
**Issues**:
- Property owner updates go live immediately
- No approval workflow
- No auto-approve timing control

**Actions Required**:
```python
# A. Create PendingPropertyChange model
# Tracks: property_id, field_changed, old_value, new_value, requested_at, approved_at
# Status: pending, approved, rejected

# B. Add AutoApprovalSettings model
# Fields: auto_approve_enabled, auto_approve_hours (choices: 3, 6, 12)
# Admin can configure per-property or globally

# C. Create approval queue view for admin
# URL: /admin/approval-queue/
# Shows all pending changes with approve/reject buttons

# D. Add Celery task for auto-approval
# Runs hourly, checks settings, auto-approves if time elapsed

# E. Update PropertyOwner dashboard
# Show "Pending Approval" status on recent changes
# Show estimated approval time
```

## 🟡 HIGH PRIORITY (After Critical)

### 4. Payment Gateway Integration
**Requirements**:
- ZygoTrip Wallet (primary)
- UPI via Paytm
- Cards via Cashfree (Stripe fallback)

**Actions Required**:
```python
# A. Create PaymentGateway abstraction layer
# File: apps/payments/gateway.py
# Classes: WalletGateway, PaytmUPIGateway, CashfreeGateway, StripeGateway
# Each implements: initiate_payment(), verify_payment(), process_refund()

# B. Create payment routing logic
# Priority: Wallet → UPI (Paytm) → Cards (Cashfree) → Stripe fallback

# C. Add wallet balance model
# Model: WalletBalance, WalletTransaction
# Track balance, debits, credits, refunds

# D. Create payment checkout flow
# URL: /payments/checkout/<booking_reference>/
# Shows: booking summary, payment options, wallet balance
# Handles: option selection, payment initiation, callback processing

# E. Add webhook handlers for each gateway
# Paytm webhook: /payments/webhook/paytm/
# Cashfree webhook: /payments/webhook/cashfree/
# Stripe webhook: /payments/webhook/stripe/
```

### 5. Room-Level Features
**Requirements**:
- Room-specific amenities (already model exists)
- Room-specific photos (already model exists)
- Just need UI integration

**Actions Required**:
```python
# A. Seed room amenities for test data
# Some rooms: jacuzzi, balcony, bathtub
# Basic rooms: standard amenities only

# B. Update room card to show room amenities
# Use room.amenities.all() instead of property.amenities.all()
# Already partially implemented, just needs testing

# C. Add room photo gallery
# Click room card → opens modal with room-specific photos
# Template: Add modal component for room photo carousel
```

## 🟢 MEDIUM PRIORITY

### 6. Hourly Stays UI
**Requirements**:
- Toggle between night/hourly stays
- Time picker for check-in/check-out
- Backend already supports stay_type

**Actions Required**:
```python
# Add toggle button on landing page
# Add time pickers (show when hourly selected)
# Update search params to include stay_type, checkin_time, checkout_time
```

### 7. Complete Google Reviews Integration
**Requirements**:
- Fetch reviews from Google Places API
- Display on detail page
- Update rating/review_count automatically

**Actions Required**:
```python
# Celery task: fetch_google_reviews(property_id)
# Updates: rating, review_count fields
# Template: Display reviews in "Reviews" tab
```

## 📋 TESTING CHECKLIST (E2E)

### Complete Booking Flow Test
```bash
# Test 1: Wallet Payment Success
1. User has ₹10,000 wallet balance
2. Books room for ₹5,000
3. Payment succeeds
4. Wallet balance → ₹5,000
5. Booking confirmed

# Test 2: Wallet Insufficient, UPI Success
1. User has ₹1,000 wallet balance
2. Books room for ₹5,000
3. Wallet insufficient → UPI selected
4. Payment via Paytm succeeds
5. Booking confirmed

# Test 3: Card Payment Success
1. User selects card payment
2. Cashfree gateway processes
3. Payment succeeds
4. Booking confirmed

# Test 4: Payment Failure Handling
1. Payment fails at gateway
2. Booking marked as "pending"
3. User notified to retry
4. Inventory NOT deducted

# Test 5: Refund Flow
1. User cancels booking (within free cancellation window)
2. Refund initiated to original payment method
3. If wallet: credited immediately
4. If UPI/card: gateway refund initiated
5. Booking status → "refunded"
```

## 📊 CURRENT STATUS SUMMARY

| Component | Status | Completion |
|-----------|--------|------------|
| Landing Page (/hotels/) | ✅ Complete | 100% |
| Auto-suggest | ✅ Complete | 100% |
| Property-Locality Links | ✅ Complete | 100% |
| Offers System | ✅ Complete | 100% |
| Recent Searches | ✅ Complete | 100% |
| Daily Deals | ✅ Complete | 100% |
| Hotel Listing Page | ✅ Functional | 95% |
| Hotel Details Page | 🟡 Needs Fixes | 60% |
| Booking Page | 🟡 Needs Fixes | 65% |
| Price Breakdown | 🔴 Not Implemented | 30% |
| Payment Gateway | 🔴 Not Implemented | 10% |
| Admin Approval | 🔴 Not Implemented | 0% |
| Wallet System | 🔴 Not Implemented | 20% |
| Room Amenities Display | 🟡 Partial | 70% |
| Google Maps | 🔴 Not Implemented | 0% |
| Hourly Stays UI | 🔴 Not Implemented | 0% |

## 🎯 RECOMMENDED NEXT STEPS (Session 2)

1. **Run meal_plan migration** ← 5 minutes
2. **Fix hotel details images** ← 30 minutes
3. **Add meal plan display** ← 15 minutes
4. **Rebuild booking page price breakdown** ← 1 hour
5. **Add Google Maps links** ← 15 minutes
6. **Create admin approval models** ← 1 hour
7. **Design payment gateway architecture** ← 2 hours
8. **Implement wallet system** ← 3 hours
9. **Test E2E booking flow** ← 2 hours

**Total Estimated Time**: ~10 hours for full implementation

## 🚀 FINAL DELIVERABLES

When complete, system will have:
- ✅ Professional OTA landing page with dynamic sections
- ✅ Area-wise property search (Madikeri, Virajpet, etc.)
- ✅ Complete price transparency (base → discounts → fees → taxes)
- ✅ Owner-driven property management
- ✅ Admin approval workflow with auto-approve settings
- ✅ Multi-gateway payment system (Wallet, UPI, Cards)
- ✅ Room-level amenities and photos
- ✅ Functional Google Maps integration
- ✅ Complete E2E tested booking flow
- ✅ Production-ready OTA platform

All data owner/admin controlled. Zero UI hacks. Real production system.
