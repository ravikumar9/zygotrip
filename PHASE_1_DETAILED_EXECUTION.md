# PHASE 1: STRUCTURE NORMALIZATION - DETAILED EXECUTION GUIDE

**Status**: Ready for Implementation  
**Duration**: Days 1-3  
**Goal**: Clean up directory structure, remove duplicates, standardize app locations  

---

## 🔍 PHASE 1 OBJECTIVES

1. **Audit** all apps in root vs `/apps/`
2. **Identify** duplicates and conflicts
3. **Delete** root-level duplicates
4. **Update** Django settings.py imports
5. **Fix** hotel app internal conflicts
6. **Verify** no breakage via tests
7. **Document** what was changed and why

---

## 📋 STEP-BY-STEP EXECUTION

### STEP 1: AUDIT ROOT-LEVEL APPS (2 hours)

#### Task 1.1: List all root apps with code
Run this to find what's at root level:

```bash
# In repo root, list all directories with models.py
ls -la | grep "^d" | awk '{print $NF}' | while read dir; do
  if [ -f "$dir/models.py" ]; then
    echo "✓ $dir/models.py exists"
    head -5 "$dir/models.py"
  fi
done
```

#### Task 1.2: Check what's in `/apps/`
```bash
# List all apps in /apps/ directory
ls -la apps/
```

#### Task 1.3: Create audit spreadsheet
Document each app:

| App Name | Location | Has Models | Duplicates | Status | Action |
|----------|----------|-----------|-----------|--------|--------|
| accounts | root | YES | NO | Keep | KEEP (unique) |
| booking | root | YES | `apps/booking/`? | UNKNOWN | CHECK |
| buses | root | ? | `apps/buses/` | UNKNOWN | CHECK |
| cabs | root | Empty? | `apps/cabs/` | Empty shell | DELETE |
| dashboard_admin | root | YES | NO | Keep | KEEP (unique) |
| dashboard_finance | root | YES | NO | Keep | KEEP (unique) |
| dashboard_owner | root | YES | NO | Keep | KEEP (unique) |
| flights | root | ? | `apps/flights/`? | UNKNOWN | CHECK |
| hotels | BOTH | YES | YES | Messy | FIX |
| meals | root | ? | UNKNOWN | UNKNOWN | CHECK |
| pricing | root | ? | UNKNOWN | UNKNOWN | CHECK |
| payments | root | ? | UNKNOWN | UNKNOWN | CHECK |
| wallet | root | ? | UNKNOWN | UNKNOWN | CHECK |
| promos | root | ? | UNKNOWN | UNKNOWN | CHECK |
| reviews | root | ? | UNKNOWN | UNKNOWN | CHECK |
| rooms | root | ? | UNKNOWN | UNKNOWN | CHECK |
| trains | root | ? | UNKNOWN | UNKNOWN | CHECK |
| registration | root | ? | UNKNOWN | UNKNOWN | CHECK |

#### Task 1.4: Check each app for code

Execute for each app in root:
```bash
# For each app directory
app="booking"
echo "=== $app ==="
echo "Models:"
wc -l "$app/models.py" 2>/dev/null || echo "No models.py"
echo "Views:"
wc -l "$app/views.py" 2>/dev/null || echo "No views.py"
echo "Services:"
wc -l "$app/services.py" 2>/dev/null || echo "No services.py"
echo "Endpoints:"
grep -c "path\|url" "$app/urls.py" 2>/dev/null || echo "No urls.py"
```

**Expected Output**:
- **Significant code** → Duplicate + needs consolidation
- **Empty or <50 lines** → Likely deprecated → DELETE
- **Unique logic** → KEEP at root only if no `/apps/` version exists

---

### STEP 2: IDENTIFY DUPLICATES & CONFLICTS (2 hours)

#### Task 2.1: Check for `/apps/` versions

For each root app with code, check:
```bash
# Example: booking app
if [ -d "apps/booking" ]; then
  echo "DUPLICATE FOUND: booking exists in both root and apps/"
  echo "Root version:"
  wc -l booking/models.py
  echo "Apps version:"
  wc -l apps/booking/models.py
  # Show git history to determine which is active
  git log --oneline booking/models.py | head -3
  git log --oneline apps/booking/models.py | head -3
fi
```

#### Task 2.2: Analyze git history

For duplicates, check which was last modified:
```bash
# Most recent commit
app="hotels"
echo "Root version:"
git log -1 --format="%ai %s" "$app/models.py" 2>/dev/null
echo "Apps version:"
git log -1 --format="%ai %s" "apps/$app/models.py" 2>/dev/null
```

**Decision Rule**:
- Most recent = KEEP this one
- Older = DELETE this one
- Same times = Check content, likely accidental duplicate

#### Task 2.3: Search for direct imports

Find code that imports from root-level apps:

```bash
# Find all imports of root-level apps
grep -r "from booking import\|from booking.\|import booking" \
  . --include="*.py" | grep -v ".pyc" | head -20

grep -r "from rooms import\|from rooms.\|import rooms" \
  . --include="*.py" | grep -v ".pyc" | head -20

# etc. for other apps
```

**Record**: Where are these imports? (important for Phase 1 updates)

---

### STEP 3: DELETE ROOT-LEVEL DUPLICATES (3 hours)

#### Decision Matrix

```
KEEP at root:
├── accounts/         (unique auth app)
├── core/             (shared utilities)
├── dashboard_admin/  (unique admin dashboard)
├── dashboard_finance/ (unique finance dashboard)
└── dashboard_owner/  (unique owner dashboard)

MOVE from root to /apps/:
├── booking/ → apps/booking/ (if different code)
├── buses/ → DELETE (in apps/buses/)
├── cabins/ → DELETE (in apps/cabs/)
├── flights/ → DELETE (likely in apps/flights/)
├── hotels/ → FIX (in both, needs conflict resolution)
├── meals/ → DELETE (if in apps/)
├── payments/ → DELETE (if in apps/)
├── pricing/ → DELETE (if in apps/)
├── promos/ → DELETE (if in apps/)
├── reviews/ → DELETE (if in apps/)
├── rooms/ → DELETE (if in apps/)
├── trains/ → DELETE (if in apps/)
├── registration/ → DELETE (deprecated?)
└── wallet/ → DELETE (if in apps/)
```

#### Task 3.1: Before deletion - backup

```bash
# Create backup of everything we're about to delete
mkdir -p _deleted_apps_backup
for app in booking buses cabs flights meals payments pricing promos reviews rooms trains registration wallet; do
  if [ -d "$app" ]; then
    cp -r "$app" "_deleted_apps_backup/$app.backup"
    echo "Backed up $app"
  fi
done

# Commit this backup
git add "_deleted_apps_backup/"
git commit -m "Backup deleted apps before consolidation"
```

#### Task 3.2: Delete empty/deprecated apps

```bash
# Remove completely empty apps (only __init__.py or apps.py)
for app in cabs registration; do
  if [ -d "$app" ]; then
    # Check if it's just empty files
    file_count=$(find "$app" -type f ! -path "*__pycache__*" | wc -l)
    if [ $file_count -lt 5 ]; then
      echo "Deleting empty app: $app"
      rm -rf "$app"
    fi
  fi
done

# Remove migrations for deleted apps
# (Only if app had no active code)
```

#### Task 3.3: Move apps with actual code

For apps with significant code at both root and `/apps/`:

```bash
# Example: booking app
# Check if root version has different code than apps version

# If they're identical:
rm -rf booking  # Delete root version

# If they're different:
# Merge code manually (prefer whichever is more recent)
# Then delete root version
```

**Process for merged apps**:
1. Compare root vs `/apps/` versions
2. Keep newer one as source of truth
3. Merge any unique code from other version
4. Delete root version
5. Update settings.py

---

### STEP 4: FIX HOTELS APP INTERNAL CONFLICTS (4 hours)

The hotels app has conflicting file/directory structure.

#### Current state (PROBLEMATIC)
```
apps/hotels/
├── selectors.py          ← OLD FILE (module)
├── selectors/            ← NEW DIR (package)
│   ├── __init__.py
│   └── ...
├── services.py           ← OLD FILE (module)
├── services/             ← NEW DIR (package)
│   ├── __init__.py
│   └── ...
├── views.py              ← OLD FILE (module)
├── views/                ← NEW DIR (package)
│   ├── __init__.py
│   └── ...
└── filters.py            ← SHOULD MOVE TO platform/search/
```

#### Task 4.1: Rename old files to preserve them

```bash
cd apps/hotels/

# Check what's in old files
echo "=== selectors.py content ==="
head -30 selectors.py

echo "=== selectors/ directory ==="
ls -la selectors/

# Rename old file to _legacy
mv selectors.py _legacy_selectors.py
mv services.py _legacy_services.py
mv views.py _legacy_views.py

# Mark them as deprecated
echo "# DEPRECATED: Old single-file modules moved to directory structure" >> _legacy_selectors.py
echo "# See selectors/ directory instead" >> _legacy_selectors.py
```

#### Task 4.2: Update imports from old files

Find what imports from old files:
```bash
cd /path/to/repo

# Find all imports
grep -r "from apps.hotels.selectors import\|from apps.hotels import.*selectors" \
  . --include="*.py" | grep -v ".pyc" | grep -v "_legacy"

grep -r "from apps.hotels.services import\|from apps.hotels import.*services" \
  . --include="*.py" | grep -v ".pyc" | grep -v "_legacy"

grep -r "from apps.hotels.views import\|from apps.hotels import.*views" \
  . --include="*.py" | grep -v ".pyc" | grep -v "_legacy"
```

**For each import found**:
1. Check what's being imported
2. Find equivalent in new `/selectors/`, `/services/`, `/views/` directories
3. Update import path
4. Test

#### Task 4.3: Create proper structure

Ensure hotels app has this structure:
```
apps/hotels/
├── models.py
├── admin.py
├── apps.py
├── urls.py              # Keep for URL routing
├── forms.py
├── constants.py
├── validators.py
│
├── selectors/           # All read queries
│   ├── __init__.py
│   ├── property.py
│   └── related.py
│
├── services/            # All write + logic
│   ├── __init__.py
│   └── property.py
│
├── api/                 # REST API
│   ├── __init__.py
│   ├── urls.py
│   ├── serializers.py
│   ├── views.py
│   └── filters.py
│
├── views/               # Legacy HTTP views (OPTIONAL)
│   ├── __init__.py
│   └── property.py
│
├── tests/               # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_selectors.py
│   ├── test_services.py
│   ├── test_api.py
│   └── test_views.py (if legacy views exist)
│
├── migrations/
├── templates/
├── management/
├── search/              # LOCAL search (move to platform/search/)
└── __init__.py
```

#### Task 4.4: Consolidate `filters.py`

This should move to unified search engine (Phase 4), but for now:

```bash
cd apps/hotels/

# Mark as deprecated
echo "# DEPRECATED: Moving to platform/search/adapters/hotel_adapter.py" >> filters.py

# Create migration file:
# 1. Copy to platform/search/adapters/hotel_adapter.py (in Phase 4)
# 2. Delete after Phase 4 is complete
```

---

### STEP 5: UPDATE DJANGO SETTINGS (2 hours)

#### Task 5.1: Current state analysis

Read existing settings:
```python
# Current settings.py lines 59-84
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # project apps - MIXED LOCATIONS
    "accounts",                    # root
    "core.apps.CoreConfig",        # root
    "apps.hotels",                 # /apps/
    "rooms",                       # root
    "meals",                       # root
    "pricing",                     # root
    "booking",                     # root (DELETE?)
    "payments",                    # root (DELETE?)
    "wallet",                      # root (DELETE?)
    "promos",                      # root (DELETE?)
    "reviews",                     # root (DELETE?)
    "apps.buses",                  # /apps/
    "apps.packages",               # /apps/
    "flights",                     # root (DELETE?)
    "trains",                      # root (DELETE?)
    "apps.cabs",                   # /apps/
    "inventory",                   # root (DELETE?)
    "dashboard_owner",             # root
    "dashboard_admin",             # root
    "dashboard_finance",           # root
    "apps.search",                 # /apps/
    "apps.owners",                 # /apps/

    # celery
    "django_celery_beat",
    "django_celery_results",
]
```

#### Task 5.2: Create new settings configuration

After Step 3 (deletes) are complete, update:

```python
# apps/hotels/apps.py, apps/buses/apps.py, etc.
# Should be: 'apps.X.apps.XConfig'

# Then update settings.py:
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Core apps (root level, special case)
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
    
    # Dashboard apps (root level, specialized)
    "dashboard_owner.apps.DashboardOwnerConfig",
    "dashboard_admin.apps.DashboardAdminConfig",
    "dashboard_finance.apps.DashboardFinanceConfig",

    # All domain apps go in /apps/
    "apps.hotels.apps.HotelsConfig",
    "apps.buses.apps.BusesConfig",
    "apps.cabs.apps.CabsConfig",
    "apps.flights.apps.FlightsConfig",
    "apps.trains.apps.TrainsConfig",
    "apps.packages.apps.PackagesConfig",
    "apps.rooms.apps.RoomsConfig",
    "apps.meals.apps.MealsConfig",
    "apps.pricing.apps.PricingConfig",
    "apps.payments.apps.PaymentsConfig",
    "apps.wallet.apps.WalletConfig",
    "apps.promos.apps.PromosConfig",
    "apps.reviews.apps.ReviewsConfig",
    "apps.inventory.apps.InventoryConfig",
    "apps.search.apps.SearchConfig",
    "apps.owners.apps.OwnersConfig",

    # Celery
    "django_celery_beat",
    "django_celery_results",
]
```

**Rule**: 
- Apps at root = `"app_name.apps.AppNameConfig"` (like accounts, core, dashboards)
- Apps in `/apps/` = `"apps.app_name.apps.AppNameConfig"` (all domain apps)

#### Task 5.3: Verify AppConfig files exist

Each app should have proper `apps.py`:

```python
# apps/hotels/apps.py should be:
from django.apps import AppConfig

class HotelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.hotels'
    verbose_name = 'Hotels'
```

Check all apps:
```bash
# For each app in /apps/:
for app in apps/*; do
  if [ -d "$app" ]; then
    echo "=== $app ==="
    cat "$app/apps.py" | grep -E "class|name ="
  fi
done
```

---

### STEP 6: VERIFY NO MIGRATIONS CREATED (2 hours)

Django will auto-detect the changes. We need to be careful:

#### Task 6.1: Check migrations state

```bash
# See what would migrate
python manage.py makemigrations --dry-run

# Should output nothing because we only moved code
# If it outputs migrations needed, we have a problem
```

#### Task 6.2: If migrations are created

```bash
# Don't commit migrations from structural changes!
# Delete any auto-created migrations:
git status | grep migrations | grep -v "__pycache__"

# For each migration:
git restore migrations/...

# We only want to commit:
# 1. Deleted directories
# 2. Updated settings.py
# 3. Updated imports
# 4. Renamed files
```

#### Task 6.3: Run migration tests

```bash
# On CLEAN database, verify migrations work
python manage.py migrate

# Should complete without errors
# If errors, debug before continuing
```

---

### STEP 7: FIX IMPORTS THROUGHOUT CODEBASE (6 hours)

This is the largest task. Apps have been moved/renamed.

#### Task 7.1: Find all imports from deleted/moved apps

```bash
# Search for imports from old locations
grep -r "from booking import\|from booking\." . --include="*.py" \
  | grep -v ".pyc" | grep -v "_deleted_apps_backup" > imports_to_fix.txt

grep -r "from rooms import\|from rooms\." . --include="*.py" \
  | grep -v ".pyc" | grep -v "_deleted_apps_backup" >> imports_to_fix.txt

grep -r "from meals import\|from meals\." . --include="*.py" \
  | grep -v ".pyc" | grep -v "_deleted_apps_backup" >> imports_to_fix.txt

# etc. for other moved apps

# Review what needs fixing
wc -l imports_to_fix.txt
head -50 imports_to_fix.txt
```

#### Task 7.2: Systematic import fix

For each line in `imports_to_fix.txt`:

**Example: booking app moved to apps/booking/**

```python
# OLD
from booking import models
from booking.models import Booking
from booking.services import create_booking

# NEW
from apps.booking import models
from apps.booking.models import Booking
from apps.booking.services import create_booking
```

#### Task 7.3: Batch find/replace (careful!)

Use sed or a script to update:

```bash
# Preview (don't execute yet)
find . -name "*.py" -type f ! -path "*/__pycache__/*" ! -path "*/.git/*" \
  -exec grep -l "from booking import\|from booking\." {} \;

# ONE BY ONE, verify then update:
# For each file:
# 1. Open in editor
# 2. Review the import
# 3. Understand what's imported
# 4. Update carefully
# 5. Test
```

**Better approach - use IDE refactoring**:
1. In VS Code: Right-click on import
2. "Go to Definition"
3. Verify location
4. Click "Update Imports" (if available)
5. Or manually fix

#### Task 7.4: Test imports after fixing

```bash
# Try importing everything
python manage.py shell

# For each formerly-moved app:
from apps.booking.models import Booking  # Should work
from apps.rooms.models import Room        # Should work
# etc.

# If any fail: find missing import and fix
```

---

### STEP 8: VERIFY TESTS PASS (3 hours)

#### Task 8.1: Run full test suite

```bash
# Full test run
pytest --tb=short

# Should pass all tests
# If failures: likely import issues from Step 7
```

#### Task 8.2: Common failures & fixes

```
ERROR: ImportError: cannot import name 'X' from 'apps.Y'
→ Fix: Check if module moved, update path

ERROR: django.core.exceptions.ImproperlyConfigured
→ Fix: Settings.py has wrong app name

ERROR: No module named 'apps.X'
→ Fix: __init__.py missing in directory
```

#### Task 8.3: Run migrations on test database

```bash
# Verify migrations work
python manage.py migrate --run-syncdb

# Should complete cleanly
```

---

### STEP 9: CREATE SUMMARY REPORT (1 hour)

Document what was changed:

```markdown
# Phase 1 Summary Report

## Changes Made

### Deleted Applications (moved to /apps/)
- booking → apps/booking/
- rooms → apps/rooms/
- meals → apps/meals/
- pricing → apps/pricing/
- payments → apps/payments/
- wallet → apps/wallet/
- promos → apps/promos/
- reviews → apps/reviews/
- trains → apps/trains/
- flights → apps/flights/
- inventory → apps/inventory/

### Deleted Empty Shells
- cabs (was empty, apps/cabs exists)
- registration (deprecated)

### Fixed Internal Conflicts
- apps/hotels/
  - selectors.py → _legacy_selectors.py (moved to selectors/ dir)
  - services.py → _legacy_services.py (moved to services/ dir)
  - views.py → _legacy_views.py (moved to views/ dir)
  - filters.py marked for Phase 4 migration

### Updated Settings.py
- Changed INSTALLED_APPS to use full paths
- All domain apps now in "apps.X.apps.XConfig" format
- Core/special apps use root format

### Import Updates
- Updated XX files with new import paths
- Verified all imports working

## Verification Results
- ✓ All tests passing
- ✓ Migrations clean
- ✓ No circular imports
- ✓ Django admin working
- ✓ Development server runs

## Remaining Work
- Phase 2: Standardize structure of all apps
- Phase 3: Extract domain layer
- Phase 4: Unify search engine
```

---

## 👀 EXPECTED RESULTS AFTER PHASE 1

### Directory Structure
```
✓ All domain apps in /apps/
✓ No duplicates
✓ One source of truth per app
```

### Settings.py
```
✓ Consistent app names
✓ All "apps.X.apps.XConfig" format
```

### Imports
```
✓ All use "from apps.X import Y"
✓ No broken imports
✓ No circular dependencies
```

### Tests
```
✓ All tests passing
✓ No import errors
✓ Migrations work cleanly
```

---

## ⚠️ RISKS & MITIGATION

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Merge conflicts | HIGH | Work on feature branch, frequent commits |
| Broken imports | HIGH | Test systematically, IDE refactoring help |
| Migration issues | MEDIUM | Test migrations on clean DB first |
| Performance regression | LOW | Monitor query counts after |
| Deployment failure | MEDIUM | Dry-run on staging first |

---

## ✅ PHASE 1 CHECKLIST

- [ ] Audit all root apps (Task 1)
- [ ] Identify duplicates (Task 2)
- [ ] Delete empty shells (Task 3)
- [ ] Move/consolidate duplicates (Task 3)
- [ ] Fix hotels internal conflicts (Task 4)
- [ ] Update settings.py (Task 5)
- [ ] Verify migrations (Task 6)
- [ ] Fix imports (Task 7)
- [ ] Run tests (Task 8)
- [ ] Create report (Task 9)
- [ ] Get approval for Phase 2

**Estimated Time**: 25-30 hours (3 full days)

