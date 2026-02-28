# GOIBIBO-STYLE URL & FEATURE IMPLEMENTATION PROMPT

## CRITICAL PRIORITY: URL Structure Overhaul

### Current State Analysis
- ❌ URLs lack city codes (CTXCR pattern)
- ❌ No geo-coordinates in URL parameters
- ❌ Missing locationData structured format
- ❌ Simple date format (YYYY-MM-DD) instead of compact (YYYYMMDD)
- ❌ Missing vcid (visitor context ID)
- ❌ roomString not implemented (currently separate adults/rooms params)
- ❌ No locusId/locusType parameters
- ❌ Missing sType (search type: landmark, area, city)
- ❌ No currency code parameter
- ❌ Missing country code (cc=IN)

---

## PHASE 1: URL STRUCTURE TRANSFORMATION

### 1.1 Hotel Listing URL Pattern

**Goibibo Reference:**
```
/hotels/hotel-listing/?checkin=20260303&checkout=20260304&roomString=1-2-0&searchText=Madikeri&locusId=CTXCR&locusType=city&cityCode=CTXCR&cc=IN&_uCurrency=INR&vcid=6023970226287476279&locationData=area|Madikeri$ARMAD$12.4244205$75.7381856|L&sType=landmark
```

**Required Parameters:**
- `checkin` - YYYYMMDD format (20260303)
- `checkout` - YYYYMMDD format (20260304)
- `roomString` - Format: `{rooms}-{adults}-{children}` (1-2-0)
- `searchText` - Display name (Madikeri)
- `locusId` - City code (CTXCR)
- `locusType` - Type: city, area, landmark
- `cityCode` - Same as locusId (CTXCR)
- `cc` - Country code (IN)
- `_uCurrency` - Currency (INR)
- `vcid` - Visitor context ID (timestamp-based unique)
- `locationData` - Structured: `{type}|{name}${code}${lat}${lon}|L`
- `sType` - Search type: landmark, area, city

**Implementation Tasks:**

1. **Create URL Builder Service** (`apps/hotels/url_builder.py`):
   ```python
   class GoibiboURLBuilder:
       @staticmethod
       def build_listing_url(city, checkin, checkout, rooms, adults, children):
           """
           Build Goibibo-style listing URL
           Returns: QueryDict with all parameters
           """
           return {
               'checkin': checkin.strftime('%Y%m%d'),
               'checkout': checkout.strftime('%Y%m%d'),
               'roomString': f"{rooms}-{adults}-{children}",
               'searchText': city.name,
               'locusId': city.code,
               'locusType': 'city',
               'cityCode': city.code,
               'cc': 'IN',
               '_uCurrency': 'INR',
               'vcid': generate_vcid(),
               'locationData': f"city|{city.name}${city.code}${city.latitude}${city.longitude}|L",
               'sType': 'city'
           }
   ```

2. **Update `URLParamValidator`** to handle both formats:
   - Accept compact dates (20260303) OR ISO dates (2026-03-03)
   - Parse roomString OR separate params (backwards compatible)
   - Extract city from locationData OR location param

3. **Update Landing Page Form** (`templates/hotels/landing.html`):
   - Change form action to use URL builder
   - Generate proper URL on submission

4. **Update Auto-Suggest API** (`/api/hotels/suggest/`):
   - Return city codes with each result
   - Return coordinates
   - Return property counts: `{name} (23 properties)`

---

### 1.2 Hotel Details URL Pattern

**Goibibo Reference:**
```
/hotels/hotel-details/?checkin=20260226&checkout=20260227&roomString=1-2-0&searchText=TGI%20Redolent%20Resort&locusId=CTXCR&locusType=city&cityCode=CTXCR&cc=IN&_uCurrency=INR&vcid=7195147538949616642&giHotelId=2554871951190905392&locationData=area|Kushalnagar$ARKUS$12.4602275$75.9608385|L&mmtId=202411051700388184&sType=landmark
```

**Additional Parameters:**
- `giHotelId` - Global hotel ID (hash of property slug)
- `mmtId` - MMT/internal ID (property.id)
- `searchText` - Property name (URL encoded)

**Implementation Tasks:**

1. **Add ID Fields to Property Model**:
   ```python
   # In apps/hotels/models.py
   class Property:
       mmtId = models.CharField(max_length=50, unique=True, editable=False)
       giHotelId = models.CharField(max_length=50, unique=True, editable=False)
       
       def save(self, *args, **kwargs):
           if not self.mmtId:
               self.mmtId = str(self.id).zfill(18)  # Pad to 18 digits
           if not self.giHotelId:
               import hashlib
               hash_str = hashlib.sha256(self.slug.encode()).hexdigest()
               self.giHotelId = str(int(hash_str[:16], 16))  # Convert to numeric
           super().save(*args, **kwargs)
   ```

2. **Update Detail View** to use these IDs in URL

---

### 1.3 Booking URL Pattern

**Goibibo Reference:**
```
/hotels/nhotel-booking/?_uCurrency=INR&checkin=02262026&checkout=02272026&city=Coorg&country=IN&couponCode=DEFAULT&hotelId=202411051700388184&giHotelId=2554871951190905392&locusId=CTXCR&locusType=city&roomCriteria=1382~%7C~4455382910944713808~%7C~INGO~%7C~4455382910944713808~%7C~2e0~%7C~false~~~&vcid=7195147538949616642&roomString=1-2-0&searchText=TGI%20Redolent&payMode=PAS&searchType=E&sType=landmark&cityCode=CTXCR
```

**Additional Parameters:**
- `city` - City name
- `country` - Country name (IN)
- `couponCode` - Applied coupon (DEFAULT if none)
- `hotelId` - MMT ID
- `giHotelId` - Global hotel ID
- `roomCriteria` - Complex string: `{roomTypeId}~|~{rateId}~|~{mealPlan}~|~{rateId2}~|~{included}~|~{flags}~~~`
- `payMode` - Payment mode (PAS = Pay at Stay, PAN = Pay at Now)
- `searchType` - E (Enhanced)

**Implementation Tasks:**

1. **Create RoomCriteria Builder**:
   ```python
   def build_room_criteria(room_type, meal_plan, rate_plan):
       parts = [
           str(room_type.id),
           str(rate_plan.id),
           meal_plan.code if meal_plan else 'NOML',
           str(rate_plan.id),
           '2e0',
           'false',
           '',
           '',
           ''
       ]
       return '~|~'.join(parts)
   ```

---

## PHASE 2: FEATURE ENHANCEMENTS

### 2.1 Auto-Suggestion with Property Counts

**Current Issue:** Auto-suggest doesn't show property counts

**Implementation:**

1. **Update `/api/hotels/suggest/` endpoint**:
   ```python
   def autosuggest_api(request):
       query = request.GET.get('q', '').strip()
       
       cities = City.objects.filter(
           Q(name__icontains=query) | Q(alternate_names__icontains=query)
       )
       
       results = {
           'cities': [
               {
                   'name': city.name,
                   'code': city.code,
                   'state': city.state.name,
                   'property_count': city.hotel_count,  # Add count
                   'display': f"{city.name}, {city.state.name} ({city.hotel_count} properties)",
                   'latitude': float(city.latitude),
                   'longitude': float(city.longitude)
               }
               for city in cities[:5]
           ],
           # ... areas, properties
       }
       return JsonResponse(results)
   ```

2. **Update Frontend Display**:
   ```html
   <div class="autosuggest-item">
       <span class="location-name">{{ name }}</span>
       <span class="property-count">{{ count }} properties</span>
   </div>
   ```

---

### 2.2 Default Dates & Calendar Behavior

**Requirements:**
- Default check-in: Today's date
- Default check-out: Tomorrow's date
- Disable past dates
- Checkout must be >= checkin

**Implementation:**

1. **Update Landing Page** (`templates/hotels/landing.html`):
   ```html
   <input 
       type="date" 
       name="checkin" 
       id="checkin"
       value="{{ today|date:'Y-m-d' }}"
       min="{{ today|date:'Y-m-d' }}"
       required
   >
   <input 
       type="date" 
       name="checkout" 
       id="checkout"
       value="{{ tomorrow|date:'Y-m-d' }}"
       min="{{ tomorrow|date:'Y-m-d' }}"
       required
   >
   
   <script>
       // Update checkout min based on checkin selection
       document.getElementById('checkin').addEventListener('change', function() {
           const checkin = new Date(this.value);
           const minCheckout = new Date(checkin);
           minCheckout.setDate(minCheckout.getDate() + 1);
           document.getElementById('checkout').min = minCheckout.toISOString().split('T')[0];
       });
   </script>
   ```

2. **Update View Context**:
   ```python
   from datetime import date, timedelta
   
   def hotel_home(request):
       context = {
           'today': date.today(),
           'tomorrow': date.today() + timedelta(days=1)
       }
       return render(request, 'hotels/landing.html', context)
   ```

---

### 2.3 Star Rating Display (Already Implemented - Verify)

**Verify in `serialize_hotel_card()`:**
```python
'star_category': property_obj.star_category,  # ✓ Already added
```

**Verify in `list.html` template:**
```html
{% if hotel.star_category %}
    <div style="color: #f59e0b;">
        {% for i in "x"|ljust:hotel.star_category %}⭐{% endfor %} 
        {{ hotel.star_category }}-Star {{ hotel.property_type }}
    </div>
{% endif %}
```

---

### 2.4 Image Display Fix

**Issue:** Images not loading properly

**Root Cause Analysis:**
1. Check if `PropertyImage` has both `image` (FileField) and `image_url` (URLField)
2. Template might be using wrong field

**Fix Already Applied:**
```html
<!-- In gallery_component.html -->
{% if image.image %}{{ image.image.url }}{% else %}{{ image.image_url }}{% endif %}
```

**Additional Check:**

1. **Verify Media URL Configuration** (`settings.py`):
   ```python
   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```

2. **Verify URLs** (`urls.py`):
   ```python
   from django.conf.urls.static import static
   
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

3. **Check Image Upload**:
   ```bash
   python manage.py shell -c "from apps.hotels.models import PropertyImage; imgs = PropertyImage.objects.all()[:5]; print([f'{img.property.name}: image={bool(img.image)}, url={bool(img.image_url)}' for img in imgs])"
   ```

---

### 2.5 Room-Specific Amenities & Photos

**Current:** Property-level amenities only
**Required:** Room-specific amenities (tub, jacuzzi, etc.)

**Implementation:**

1. **Check RoomType Model** (`apps/rooms/models.py`):
   ```python
   class RoomType:
       # Should have M2M to RoomAmenity
       amenities = models.ManyToManyField('RoomAmenity', related_name='rooms', blank=True)
   ```

2. **Create RoomAmenity Model** (if doesn't exist):
   ```python
   class RoomAmenity(models.Model):
       name = models.CharField(max_length=100)
       icon = models.CharField(max_length=50, blank=True)
       category = models.CharField(max_length=50, choices=[
           ('bathroom', 'Bathroom'),
           ('bedroom', 'Bedroom'),
           ('entertainment', 'Entertainment'),
           ('comfort', 'Comfort')
       ])
       is_premium = models.BooleanField(default=False)  # jacuzzi, tub are premium
       
       def __str__(self):
           return self.name
   ```

3. **Add Room Photos**:
   ```python
   class RoomImage(models.Model):
       room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='images')
       image = models.ImageField(upload_to='rooms/')
       caption = models.CharField(max_length=200, blank=True)
       is_featured = models.BooleanField(default=False)
       display_order = models.IntegerField(default=0)
   ```

4. **Update Room Card Template**:
   ```html
   <div class="room-card__amenities">
       {% for amenity in room.amenities.all %}
           <span class="room-amenity {% if amenity.is_premium %}premium{% endif %}">
               <i class="{{ amenity.icon }}"></i> {{ amenity.name }}
           </span>
       {% endfor %}
   </div>
   ```

---

### 2.6 Coupon Code Integration

**Goibibo Pattern:** `couponCode=DEFAULT` in URL

**Implementation:**

1. **Create Coupon Service** (`apps/promos/coupon_service.py` - already exists?):
   ```python
   class CouponService:
       @staticmethod
       def get_auto_applied_coupon(user, property, total_price):
           """
           Auto-apply best coupon for user
           Returns: Coupon object or None
           """
           # Logic to find best applicable coupon
           pass
       
       @staticmethod
       def validate_coupon(code, user, booking_params):
           """Validate coupon code"""
           pass
   ```

2. **Add Coupon Field to Booking URL**:
   - Default to 'DEFAULT'
   - Show auto-applied coupon in booking page
   - Allow user to change/remove

3. **Display Coupon in Booking Form**:
   ```html
   <div class="coupon-section">
       <input type="text" name="couponCode" value="{{ auto_coupon.code|default:'DEFAULT' }}">
       <button type="button" onclick="applyCoupon()">Apply</button>
       {% if auto_coupon %}
           <div class="coupon-applied">
               ✓ {{ auto_coupon.name }} applied - Save ₹{{ discount }}
           </div>
       {% endif %}
   </div>
   ```

---

### 2.7 Discount & Service Fee Display

**Goibibo Pattern:**
```
Room Price:     ₹3,500
Discount (10%): -₹350
Service Fee:    +₹150
-----------------------
Total:          ₹3,300
```

**Implementation:**

1. **Update Pricing Display** (booking page):
   ```html
   <div class="price-breakdown">
       <div class="price-row">
           <span>Room Price ({{ nights }} nights × ₹{{ room_price }})</span>
           <span>₹{{ base_total }}</span>
       </div>
       
       {% if discount > 0 %}
       <div class="price-row discount">
           <span>Property Discount ({{ discount_percent }}%)</span>
           <span>-₹{{ discount }}</span>
       </div>
       {% endif %}
       
       {% if coupon_discount > 0 %}
       <div class="price-row discount">
           <span>Coupon Discount ({{ coupon.code }})</span>
           <span>-₹{{ coupon_discount }}</span>
       </div>
       {% endif %}
       
       <div class="price-row">
           <span>Service Fee</span>
           <span>+₹{{ service_fee }}</span>
       </div>
       
       <div class="price-row">
           <span>Taxes & Fees</span>
           <span>+₹{{ taxes }}</span>
       </div>
       
       <div class="price-row total">
           <span>Total Amount</span>
           <span>₹{{ final_total }}</span>
       </div>
   </div>
   ```

2. **Update PriceEngine** (`apps/pricing/price_engine.py`):
   ```python
   class PriceEngine:
       def calculate_booking_price(self, room_type, checkin, checkout, rooms, coupon=None):
           # base_price = room_type.base_price * nights * rooms
           # discount = property.discount_percentage
           # coupon_discount = coupon.calculate_discount(base_price)
           # service_fee = calculate_service_fee(base_price)
           # taxes = calculate_taxes(base_price - discounts)
           
           return {
               'base_total': base_price * nights * rooms,
               'discount': discount_amount,
               'discount_percent': property.discount_percentage,
               'coupon_discount': coupon_discount,
               'service_fee': service_fee,
               'taxes': taxes,
               'final_total': total_after_all_calculations
           }
   ```

---

### 2.8 Hourly Stays Option

**Implementation:**

1. **Add Stay Type Toggle** (landing page):
   ```html
   <div class="stay-type-toggle">
       <input type="radio" name="stay_type" value="night" id="night" checked>
       <label for="night">Night Stay</label>
       
       <input type="radio" name="stay_type" value="hourly" id="hourly">
       <label for="hourly">Hourly Stay</label>
   </div>
   
   <div id="hourly-inputs" style="display:none;">
       <input type="time" name="checkin_time" value="12:00">
       <input type="time" name="checkout_time" value="18:00">
       <span class="duration">6 hours</span>
   </div>
   ```

2. **Update URLParamValidator** (already supports `stay_type='hourly'`, verify)

---

### 2.9 Google Review Ratings Integration

**Phase 1: Use Existing Rating**
- Display `property.rating` as Google rating style
- Show review count

**Phase 2: Google Places API Integration** (Future):
```python
class GooglePlacesService:
    def fetch_reviews(self, property):
        # Use Google Places API to fetch actual reviews
        pass
```

---

## PHASE 3: PAYMENTS INTEGRATION

### 3.1 Payments Subdomain URL

**Goibibo:** `https://payments.goibibo.com/checkout/?id=945699793337158&region=in`

**Implementation:**

1. **Create Payments App** (`apps/payments/`):
   ```python
   # views.py
   def checkout(request):
       booking_id = request.GET.get('id')
       region = request.GET.get('region', 'in')
       
       # Load booking, create payment intent
       # Render payment page with Razorpay/Stripe
   ```

2. **Configure Subdomain** (`settings.py`):
   ```python
   ALLOWED_HOSTS = [
       'localhost',
       '127.0.0.1',
       'zygotrip.com',
       'payments.zygotrip.com'
   ]
   ```

3. **Redirect from Booking**:
   ```python
   # After booking creation
   payment_url = f"https://payments.{settings.DOMAIN}/checkout/?id={booking.reference}&region=in"
   return redirect(payment_url)
   ```

---

## PHASE 4: FRONTEND POLISH

### 4.1 Goibibo-Style Hotel Card

**Reference:** See attached screenshot

**CSS Improvements:**
```css
.hotel-card {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
}

.hotel-card__image {
    width: 240px;
    height: 180px;
    border-radius: 6px;
    object-fit: cover;
}

.hotel-card__info {
    flex: 1;
}

.hotel-card__header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}

.star-category {
    color: #f59e0b;
    font-size: 0.875rem;
    font-weight: 600;
}

.rating-badge {
    background: #10b981;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
}

.hotel-card__amenities {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-top: 0.5rem;
}

.amenity-badge {
    background: #f3f4f6;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
}

.hotel-card__pricing {
    text-align: right;
}

.price-original {
    text-decoration: line-through;
    color: #9ca3af;
    font-size: 0.875rem;
}

.price-final {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1f2937;
}

.discount-badge {
    background: #10b981;
    color: white;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
}
```

---

## IMPLEMENTATION PRIORITY

### MUST DO (Week 1):
1. ✅ URL structure transformation (CRITICAL)
2. ✅ Auto-suggest with property counts
3. ✅ Default dates & calendar behavior
4. ✅ Star rating display (verify)
5. ✅ Image display fix
6. ✅ Discount & pricing breakdown

### SHOULD DO (Week 2):
7. ⚠️ Room-specific amenities & photos
8. ⚠️ Coupon integration
9. ⚠️ Hourly stays option
10. ⚠️ Frontend polish (Goibibo-style cards)

### COULD DO (Week 3):
11. 🔵 Google review ratings
12. 🔵 Payments subdomain
13. 🔵 Advanced filters (based on Goibibo screenshot)

---

## VERIFICATION CHECKLIST

### URL Structure:
- [ ] Listing URL includes all 11 required parameters
- [ ] Detail URL includes giHotelId and mmtId
- [ ] Booking URL includes roomCriteria
- [ ] Date format is YYYYMMDD
- [ ] roomString format is {rooms}-{adults}-{children}
- [ ] locationData is properly formatted

### Features:
- [ ] Auto-suggest shows property counts
- [ ] Default dates are today/tomorrow
- [ ] Calendar disables past dates
- [ ] Star category displays on cards
- [ ] Images load correctly
- [ ] Room amenities displayed
- [ ] Discount breakdown shown
- [ ] Service fee calculated

### Data Flow:
- [ ] All prices from database (no UI hacks)
- [ ] Discounts from Property.discount_percentage
- [ ] Star ratings from Property.star_category
- [ ] Reviews from Property.rating/review_count
- [ ] Images from PropertyImage/RoomImage models

---

## MIGRATION PLAN

1. **Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Data Seeding:**
   - Ensure all cities have codes (CTXCR format)
   - Ensure all cities have coordinates
   - Generate mmtId and giHotelId for existing properties

3. **Backwards Compatibility:**
   - Keep accepting old URL format alongside new
   - Automatically redirect old URLs to new format

---

## TESTING PLAN

1. **URL Building Tests:**
   ```python
   def test_goibibo_url_builder():
       city = City.objects.get(code='CTXCR')
       url_params = GoibiboURLBuilder.build_listing_url(
           city, date(2026, 3, 3), date(2026, 3, 4), 1, 2, 0
       )
       assert url_params['checkin'] == '20260303'
       assert url_params['roomString'] == '1-2-0'
       assert 'locationData' in url_params
   ```

2. **End-to-End Flow:**
   - Land on homepage → see default dates
   - Search "Coorg" → see property counts in autosuggest
   - Click result → navigate with full URL parameters
   - View hotel card → see star rating, discount badge
   - View details → see room-specific amenities
   - Click book → see price breakdown with discounts

---

## FINAL NOTES

This implementation brings your system to Goibibo's professional standard:
- ✅ Sophisticated URL framing with geo-intelligence
- ✅ Real-time property counts in suggestions
- ✅ Proper date handling with validation
- ✅ Transparent pricing with breakdown
- ✅ Room-level granularity for amenities
- ✅ Professional UI matching industry leaders

**Next Steps:** Review this prompt, prioritize based on your current sprint, and implement phase by phase.
