# PHASE 9 - QUICK START & VERIFICATION GUIDE

## 30-Second System Check

```bash
cd /path/to/zygotrip
python phase9_validation.py
```

**Expected Output**: `Result: 7/7 tests passed`

---

## Quick Verification Checklist

### ✅ Can I Start the Django Server?
```bash
python manage.py runserver 0.0.0.0:8000
```
Expected: Server starts without errors and binds to port 8000

### ✅ Can I Access the Health Endpoint?
```bash
curl http://localhost:8000/health/
```
Expected: JSON response with `"status": "ok"` and `"database": "connected"`

### ✅ Can I Access Django Admin?
```
http://localhost:8000/admin/
```
Expected: Login page appears, all models visible in admin

### ✅ Can I Access Marketplace?
```
http://localhost:8000/hotels/
```
Expected: Hotels listing page loads

### ✅ Are All Models Registered?
In Django admin, verify these are visible:
- ✅ Booking
- ✅ Booking Guest
- ✅ Booking Price Breakdown
- ✅ Booking Status History
- ✅ Settlement
- ✅ Settlement Line Item
- ✅ Payment

### ✅ Are All Dashboards Accessible?
```
http://localhost:8000/owner/dashboard/
http://localhost:8000/admin/dashboard/
http://localhost:8000/finance/dashboard/
```
Expected: Pages load without errors

---

## Development vs Production Settings

### Development (DEBUG=True, LOCAL)
| Setting | Value | Why |
|---------|-------|-----|
| SSL Redirect | OFF | No HTTPS needed locally |
| Secure Cookies | OFF | Can test without HTTPS |
| HSTS | OFF | No browser HSTS requirement |
| Celery Tasks | Eager | No worker needed |
| Celery Beat | Disabled | No scheduler needed |
| External Services | None required | All embedded/simulated |

### Production (DEBUG=False, DEPLOYED)
| Setting | Value | Why |
|---------|-------|-----|
| SSL Redirect | ON | Force HTTPS everywhere |
| Secure Cookies | ON | Cookies only over HTTPS |
| HSTS | ON (1 year) | Browser enforces HTTPS |
| Celery Tasks | Async | Use Redis broker |
| Celery Beat | Enabled | Run scheduled tasks |
| External Services | Required | Redis, PostgreSQL, email |

---

## Common Tasks

### Test Database Connection
```bash
python manage.py dbshell
# Then type: SELECT 1;
# Should return 1
```

### Check Migrations Status
```bash
python manage.py showmigrations | grep "[ ]"
# Should show nothing (all applied)
```

### Create a Test Booking (Manual)
```bash
python manage.py shell
```
```python
from apps.booking.models import Booking
from apps.hotels.models import Property, RoomType
from apps.accounts.models import User
from datetime import datetime, timedelta

# Get test data
user = User.objects.first()
prop = Property.objects.first()
room_type = prop.room_types.first()

# Create booking
booking = Booking.objects.create(
    property=prop,
    room_type=room_type,
    user=user,
    check_in=datetime.now().date() + timedelta(days=1),
    check_out=datetime.now().date() + timedelta(days=3),
    total_amount=5000,
    status='HOLD'
)

print(f"Booking created: {booking.id}")
print(f"Status: {booking.status}")
```

### Test Settlement Generation (Manual)
```bash
python manage.py shell
```
```python
from apps.booking.settlement_services import generate_settlement
from apps.hotels.models import Property
from datetime import datetime, timedelta, date

prop = Property.objects.first()
settlement = generate_settlement(
    prop,
    date.today() - timedelta(days=30),
    date.today()
)

print(f"Settlement created: {settlement.id}")
print(f"Total payable: {settlement.total_payable}")
```

### Clear Test Data
```bash
python manage.py flush --noinput
# Then seed fresh data
python manage.py seed_ota_data
```

---

## Troubleshooting

### Server Won't Start
```bash
# Check for port conflicts
lsof -i :8000  # Unix/Mac
netstat -ano | findstr :8000  # Windows

# If port in use, use different port
python manage.py runserver 8001
```

### Database Errors
```bash
# Verify migrations are applied
python manage.py migrate --check

# Show migration status
python manage.py showmigrations

# Manually apply migrations
python manage.py migrate
```

### Model Not in Admin
```bash
# Check admin registration
python manage.py shell
from django.contrib import admin
from django.contrib.admin.sites import site
site.registry  # Should list all registered models
```

### Celery Tasks Creating Issues
```bash
# Disable Celery in DEBUG mode - this is automatic with Phase 9
# Tasks run eagerly instead

# To manually trigger a task:
python manage.py shell
from core.tasks import release_expired_booking_holds
result = release_expired_booking_holds()
print(result)
```

### URL Path Not Found
```bash
# Check all registered URLs
python manage.py shell
from django.urls import get_resolver
resolver = get_resolver()
[str(p.pattern) for p in resolver.url_patterns]
```

---

## Performance Tips

### Speed Up Development Tests
```bash
# Use in-memory database (SQLite in :memory:)
# Already configured for tests

# Run specific test
python manage.py test apps.booking.tests.TestBooking
```

### Monitor Database Queries
```python
# In Django shell
from django.test.utils import override_settings
from django.db import connection, reset_queries

# In your code:
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    # Your code here
    pass

print(f"Queries executed: {len(context)}")
for q in context:
    print(q['sql'])
```

### Clear Stale Data
```bash
# Delete old bookings
python manage.py shell
```
```python
from apps.booking.models import Booking
from datetime import datetime, timedelta

old_bookings = Booking.objects.filter(
    created_at__lt=datetime.now() - timedelta(days=7)
)
old_bookings.delete()
```

---

## Phase 9 Validation Breakdown

### Test 1: Database Connection
- **What**: Verifies database is running and accessible
- **Pass Condition**: SELECT 1 executes successfully
- **Action if Fails**: Check PostgreSQL/MySQL/SQLite is running

### Test 2: Debug Mode Settings
- **What**: Verifies safe dev settings are active
- **Pass Condition**: SSL/cookies disabled when DEBUG=True
- **Action if Fails**: Check settings.py DEBUG configuration

### Test 3: Celery Configuration
- **What**: Verifies Celery behaves correctly for environment
- **Pass Condition**: Eager execution enabled in DEBUG mode
- **Action if Fails**: Check CELERY_TASK_ALWAYS_EAGER in settings

### Test 4: Model Registration
- **What**: Verifies all models are accessible in database
- **Pass Condition**: Can query Booking, Payment, Settlement tables
- **Action if Fails**: Run `python manage.py migrate`

### Test 5: URL Configuration
- **What**: Verifies all routes are registered
- **Pass Condition**: Can reverse all dashboard URLs
- **Action if Fails**: Check urls.py includes all app URLs

### Test 6: Static Files
- **What**: Verifies static file serving is configured
- **Pass Condition**: STATIC_URL and STATIC_ROOT are set
- **Action if Fails**: Check settings.py STATIC configuration

### Test 7: Migrations
- **What**: Verifies database schema is current
- **Pass Condition**: All migrations applied (0 pending)
- **Action if Fails**: Run `python manage.py migrate --noinput`

---

## Success Indicators

### ✅ Phase 9 is Successful When:
1. `python phase9_validation.py` returns 7/7 tests passed
2. `python manage.py runserver` starts without errors
3. `curl http://localhost:8000/health/` returns JSON with "ok" status
4. Django admin loads at `/admin/` without errors
5. All dashboards accessible without 404/500 errors
6. No circular import errors in console
7. Database contains all expected tables (109 migrations applied)

### ❌ Phase 9 Needs Fixing If:
- Validation script shows < 7/7 tests passing
- Server crashes on startup
- Health endpoint returns error
- Admin console shows missing models
- Database connection fails
- URLs return 404 errors
- Import errors appear in console

---

## Getting Help

### Check Logs
```bash
# Django development server logs (in console)
python manage.py runserver

# Database logs (if using PostgreSQL)
# Check PostgreSQL log files

# Application logs
tail -f logs/zygotrip.log
```

### Run Debug Mode
```bash
# Add debug prints to views
import logging
logger = logging.getLogger('zygotrip')
logger.debug("Custom debug message")

# Check messages in console
python manage.py runserver --verbosity 3
```

### Reset Everything
```bash
# WARNING: This deletes all data
python manage.py flush --noinput

# Re-apply migrations
python manage.py migrate

# Seed test data
python manage.py seed_ota_data

# Run validation
python phase9_validation.py
```

---

## Phase 9 Focus Areas

### What Phase 9 Improved:
1. ✅ Local development safety (SAFE DEV MODE)
2. ✅ Deployment monitoring (HEALTH CHECK)
3. ✅ URL wiring verification (URL VALIDATION)
4. ✅ Admin interface completeness (MODEL REGISTRATION)
5. ✅ System integrity checks (IMPORT VALIDATION)
6. ✅ Database consistency (MIGRATION VALIDATION)
7. ✅ Static file serving (STATIC FILES)

### What Phase 9 Did NOT Change:
- ❌ Booking atomic transaction logic
- ❌ Hold expiry mechanism
- ❌ State machine enforcement
- ❌ Financial calculations
- ❌ Settlement system
- ❌ Payment webhook handling
- ❌ Refund engine
- ❌ Inventory locking
- ❌ Dashboard features
- ❌ Security hardening
- ❌ Founder metrics

**All business logic preserved. Only integration improved.**

---

## One-Command Status Check

```bash
echo "=== PHASE 9 STATUS ===" && python phase9_validation.py && echo "" && echo "✅ System operational and ready for testing"
```

---

**Last Updated**: February 24, 2026  
**Phase**: 9 - Integration Stabilization  
**Status**: ✅ All Systems Go  
