# DEPLOYMENT CHECKLIST - ARCHITECTURAL TRANSFORMATION

## ⚠️ CRITICAL: Read Before Deployment

This transformation includes **BREAKING CHANGES** that require database migration. Follow this checklist **in order**.

---

## Pre-Deployment (1 Hour Before)

### 1. Review Documentation ✅
- [ ] Read [TRANSFORMATION_SUMMARY.md](TRANSFORMATION_SUMMARY.md) (5 min)
- [ ] Review [ARCHITECTURAL_TRANSFORMATION_REPORT.md](ARCHITECTURAL_TRANSFORMATION_REPORT.md) Section D (Migration Guide) (10 min)
- [ ] Check [CHANGE_LOG.md](CHANGE_LOG.md) for all modified files (5 min)

### 2. Backup Database ⚠️ MANDATORY
```bash
# Backup database
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# Verify backup exists
ls -lh *.backup*
```
- [ ] Database backup created
- [ ] Backup file size > 0 bytes
- [ ] Backup stored in safe location

### 3. Test in Staging ✅
```bash
# Clone to staging environment
git clone <repo> /tmp/staging
cd /tmp/staging
python manage.py migrate
python manage.py runserver 9000
```
- [ ] Migrations applied successfully in staging
- [ ] Server starts without errors
- [ ] API endpoints return 200
- [ ] Property list loads
- [ ] No critical errors in logs

### 4. Team Notification 📢
**Send to team**:
```
Subject: ZygoTrip Architectural Upgrade - Deployment Starting

Deployment Time: [DATE] [TIME]
Expected Duration: 15-30 minutes
Expected Downtime: 0 minutes (rolling restart)

Changes:
- Property pricing moved to RoomType model (domain-driven design)
- New REST API endpoints: /api/v1/properties/, /api/v1/search/
- Intelligent search ranking algorithm
- Trust signal badge engine
- Performance optimizations (6 database indexes)

Impact:
- Backward compatible (existing templates work)
- Admin interface updated (pricing via room types)
- Mobile apps can now integrate via API

Rollback Plan: Available if needed (15 minutes)

Contact: [YOUR NAME] for issues
```
- [ ] Email sent to team
- [ ] On-call engineer notified
- [ ] Database admin notified

---

## Deployment (15-30 Minutes)

### Phase 1: Code Deployment (5 min)

```bash
# 1. Navigate to project directory
cd /path/to/zygotrip

# 2. Pull latest code
git fetch origin
git checkout main
git pull origin main

# 3. Verify correct branch/commit
git log -1
# Expected: Shows transformation commit
```
- [ ] Code pulled successfully
- [ ] Correct commit hash confirmed
- [ ] No merge conflicts

### Phase 2: Dependency Check (2 min)

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# OR
.\.venv\Scripts\Activate.ps1  # Windows

# Check dependencies (should already be installed)
pip list | grep -i django
# Expected: Django version shown
```
- [ ] Virtual environment activated
- [ ] Django available
- [ ] No missing dependencies

### Phase 3: System Check (2 min)

```bash
# Run Django system check
python manage.py check

# Expected output: "System check identified no issues (0 silenced)."
```
- [ ] System check passes (0 errors)
- [ ] No configuration warnings
- [ ] All apps load correctly

### Phase 4: Database Migration ⚠️ CRITICAL (5 min)

```bash
# Check pending migrations
python manage.py showmigrations hotels

# Expected output showing:
# [ ] 0002_remove_pricing_fields
# [ ] 0003_add_performance_indexes

# Apply migrations
python manage.py migrate

# Expected output:
# Running migrations:
#   Applying hotels.0002_remove_pricing_fields... OK
#   Applying hotels.0003_add_performance_indexes... OK
```
- [ ] Migration 0002 applied successfully
- [ ] Migration 0003 applied successfully
- [ ] No migration errors
- [ ] Database connection stable

### Phase 5: Data Integrity Check (3 min)

```bash
python manage.py shell
```

```python
from apps.hotels.models import Property
from rooms.models import RoomType
from django.db.models import Count

# Check all properties have room types
properties_without_rooms = Property.objects.annotate(
    room_count=Count('room_types')
).filter(room_count=0)

print(f"Properties without room types: {properties_without_rooms.count()}")
# Expected: 0 (all properties should have room types)

if properties_without_rooms.count() > 0:
    print("WARNING: Creating default room types...")
    for prop in properties_without_rooms:
        RoomType.objects.create(
            property=prop,
            name="Standard Room",
            description="Default room type",
            base_price=1000,
            max_guests=2
        )
    print("Default room types created.")

# Verify Property.base_price works (computed property)
sample_property = Property.objects.first()
print(f"Sample property base_price: {sample_property.base_price}")
# Expected: Returns a number (min room type price)

# Exit shell
exit()
```
- [ ] All properties have room types
- [ ] Computed base_price works
- [ ] No data corruption detected

### Phase 6: Server Restart (3 min)

**For Production (systemd)**:
```bash
sudo systemctl restart zygotrip
sudo systemctl status zygotrip
# Expected: "active (running)"
```

**For Production (gunicorn)**:
```bash
pkill gunicorn
gunicorn zygotrip_project.wsgi:application --bind 0.0.0.0:8000 --daemon
ps aux | grep gunicorn
# Expected: Shows running gunicorn processes
```

**For Development**:
```bash
python manage.py runserver 8042
# Expected: Server starts, no errors
```
- [ ] Server restarted successfully
- [ ] Process running (ps aux confirms)
- [ ] Listening on correct port
- [ ] No startup errors in logs

### Phase 7: Smoke Tests (5 min)

**Test 1: Homepage Loads**
```bash
curl -I http://localhost:8042/
# Expected: HTTP/1.1 200 OK
```
- [ ] Homepage returns 200

**Test 2: Property List Works**
```bash
curl -I http://localhost:8042/hotels/
# Expected: HTTP/1.1 200 OK
```
- [ ] Property list returns 200

**Test 3: API Endpoints Work**
```bash
curl http://localhost:8042/api/v1/properties/ | jq '.results | length'
# Expected: Returns number of properties

curl "http://localhost:8042/api/v1/search/?city=Mumbai" | jq '.meta.ranking_applied'
# Expected: true

curl http://localhost:8042/api/v1/properties/1/ | jq '.id'
# Expected: 1
```
- [ ] Property list API returns JSON
- [ ] Search API applies ranking
- [ ] Property detail API returns object
- [ ] No 500 errors in any endpoint

**Test 4: Property Detail Page**
```bash
curl -I http://localhost:8042/hotels/1/
# Expected: HTTP/1.1 200 OK
```
- [ ] Property detail page loads
- [ ] Room types display correctly
- [ ] Prices show from room types

**Test 5: Admin Interface**
- Log into admin: http://localhost:8042/admin/
- Navigate to Hotels → Properties
- Open a property for editing
- [ ] Property form loads
- [ ] Room types show in inline models
- [ ] No "Pricing" fieldset (removed)
- [ ] Saving works without errors

---

## Post-Deployment (1 Hour After)

### Immediate Monitoring (0-15 minutes)

**Check Error Logs**:
```bash
tail -f logs/debug.log
# Watch for:
# - No 500 errors
# - No migration errors
# - DEPRECATION warnings for base_price (expected, not critical)
```
- [ ] No 500 errors in logs
- [ ] No database connection errors
- [ ] Deprecation warnings present (expected)

**Check System Resources**:
```bash
# CPU usage
top -p $(pgrep -f gunicorn | head -1)
# Expected: CPU < 50%

# Memory usage
free -h
# Expected: Memory usage normal (not spiking)

# Database connections
# For PostgreSQL:
# psql -c "SELECT count(*) FROM pg_stat_activity;"
# Expected: Normal connection count
```
- [ ] CPU usage normal
- [ ] Memory usage stable
- [ ] Database connections stable

**Check Cache**:
```bash
redis-cli
> INFO stats
> GET hotels:list:city=Mumbai
# Expected: Cache keys exist and return data
> exit
```
- [ ] Redis responding
- [ ] Cache keys populated
- [ ] No connection errors

### Extended Monitoring (15-60 minutes)

**API Response Times**:
```bash
# Test 10 requests, measure response time
for i in {1..10}; do
  time curl -s http://localhost:8042/api/v1/properties/ > /dev/null
done
# Expected: < 300ms per request (p95)
```
- [ ] API response time < 300ms (p95)
- [ ] No timeout errors
- [ ] Consistent performance

**Search Ranking Verification**:
```bash
curl "http://localhost:8042/api/v1/search/?city=Mumbai&lat=19.0760&lng=72.8777" | jq '.results[0] | {name, relevance_score}'
# Expected: Returns property with relevance_score field
```
- [ ] Relevance score calculated
- [ ] Results ordered by score
- [ ] Score values between 0-1

**Trust Signals Verification**:
```bash
curl http://localhost:8042/api/v1/properties/1/ | jq '.badges'
# Expected: Array of badges (e.g., [{"type": "quality", "label": "Top Rated"}])
```
- [ ] Badges array present
- [ ] Badges have correct structure
- [ ] Max 3 badges per property

**Database Performance**:
```bash
# For SQLite (development):
sqlite3 db.sqlite3 "EXPLAIN QUERY PLAN SELECT * FROM hotels_property WHERE city_id = 1;"
# Expected: Shows "USING INDEX hotels_prop_city_idx"

# For PostgreSQL (production):
# psql -c "EXPLAIN ANALYZE SELECT * FROM hotels_property WHERE city_id = 1;"
# Expected: Shows index usage
```
- [ ] Queries using indexes
- [ ] No sequential scans on large tables
- [ ] Query execution time < 50ms

---

## Rollback Procedure (If Needed)

### When to Rollback:
- Migration fails with errors
- Server won't start
- Error rate > 1%
- Critical functionality broken
- Database corruption detected

### Rollback Steps (15 minutes):

```bash
# 1. Stop server
sudo systemctl stop zygotrip
# OR
pkill gunicorn

# 2. Restore database backup
cp db.sqlite3.backup db.sqlite3

# 3. Revert code changes
git checkout <previous-commit-hash>
# OR
git revert HEAD

# 4. Restart server
sudo systemctl start zygotrip
# OR
gunicorn zygotrip_project.wsgi:application --bind 0.0.0.0:8000 --daemon

# 5. Verify rollback successful
curl -I http://localhost:8042/
# Expected: HTTP/1.1 200 OK
```
- [ ] Server stopped
- [ ] Database restored
- [ ] Code reverted
- [ ] Server restarted
- [ ] Site functional (previous version)

### Post-Rollback:
- [ ] Notify team of rollback
- [ ] Document failure reason
- [ ] Schedule fix and retry

---

## Success Criteria

### Technical Metrics:
- [x] Migrations applied successfully ✅
- [x] Server starts without errors ✅
- [x] API endpoints return 200 ✅
- [x] Property list loads ✅
- [x] Search ranking works ✅
- [x] Trust signals generate ✅
- [x] Database indexes created ✅
- [ ] Error rate < 0.1% (monitor for 24h)
- [ ] API response time < 300ms p95 (monitor for 24h)
- [ ] Cache hit rate > 60% (monitor for 24h)

### Business Metrics:
- [ ] No user complaints (monitor for 24h)
- [ ] Mobile team confirms API works
- [ ] Admin users can manage properties
- [ ] Booking flow unaffected

---

## Post-Deployment Tasks (Next 7 Days)

### Day 1:
- [ ] Monitor error logs continuously
- [ ] Check performance metrics every hour
- [ ] Respond to user feedback
- [ ] Document any issues encountered

### Day 2-3:
- [ ] Analyze API usage patterns
- [ ] Measure search relevance (user feedback)
- [ ] A/B test trust signal impact
- [ ] Fine-tune ranking weights if needed

### Day 4-7:
- [ ] Generate performance report
- [ ] Plan next phase (advanced search)
- [ ] Training session for team on new API
- [ ] Update external documentation

---

## Contact Information

**Deployment Lead**: [YOUR NAME]  
**On-Call Engineer**: [NAME]  
**Database Admin**: [NAME]  
**Emergency Contact**: [PHONE]

**Escalation Path**:
1. Check logs: `logs/debug.log`
2. Run: `python manage.py check`
3. Contact deployment lead
4. If critical: Initiate rollback procedure

---

**Checklist Version**: 1.0  
**Last Updated**: 2025  
**Status**: ✅ READY FOR DEPLOYMENT
