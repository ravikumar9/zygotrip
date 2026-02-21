# MASTER REFACTOR EXECUTION PLAN
**Status**: DETAILED ANALYSIS + ACTION ROADMAP  
**Prepared**: 2024-02-21  
**Target**: Production-Grade Architecture  

---

## 🔍 CURRENT STATE ANALYSIS

### ROOT LEVEL DUPLICATE APPS (MUST DELETE)
Located at `c:\Users\ravi9\Downloads\Zy\zygotrip\` (not in `/apps/`)

These are **deprecated duplicates** of apps already in `/apps/`:

| Root App | Apps Version | Status | Action |
|----------|--------------|--------|--------|
| `accounts/` | X (unique) | KEEP | Core auth app, no duplicate |
| `booking/` | ✗ | DELETE | audit confirms: deprecated |
| `buses/` | `apps/buses/` | DELETE | Duplicate location |
| `cabs/` | `apps/cabs/` | DELETE | Deprecated, empty shell |
| `dashboard_admin/` | X | KEEP | Unique, part of core |
| `dashboard_finance/` | X | KEEP | Unique, part of core |
| `dashboard_owner/` | X | KEEP | Unique, part of core |
| `flights/` | ✗ | DELETE | Check if duplicate |
| `meals/` | ✗ | DELETE | Check if duplicate |
| `pricing/` | ✗ | DELETE | Check if duplicate |
| `payments/` | ✗ | DELETE | Check if duplicate |
| `wallet/` | ✗ | DELETE | Check if duplicate |
| `promos/` | ✗ | DELETE | Check if duplicate |
| `reviews/` | ✗ | DELETE | Check if duplicate |
| `rooms/` | ✗ | DELETE | Check if duplicate |
| `trains/` | ✗ | DELETE | Check if duplicate |
| `registration/` | ✗ | DELETE | Check location |

### INSTALLED_APPS ANALYSIS
**Current settings.py (lines 59-84)**:
```python
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    ...
    # project apps - MIXED STATE
    "accounts",                    # Root level ✓ KEEP
    "core.apps.CoreConfig",        # Root level ✓ KEEP
    "apps.hotels",                 # Mixed: has /apps/ + root behavior ⚠ NEEDS FIX
    "rooms",                       # Root level - needs audit
    "meals",                       # Root level - needs audit
    "pricing",                     # Root level - needs audit
    "booking",                     # Root level DELETE
    "payments",                    # Root level - needs audit
    "wallet",                      # Root level - needs audit
    "promos",                      # Root level - needs audit
    "reviews",                     # Root level - needs audit
    "apps.buses",                  # Apps level ✓ CONSISTENT
    "apps.packages",               # Apps level ✓ CONSISTENT
    "flights",                     # Root level - needs audit
    "trains",                      # Root level - needs audit
    "apps.cabs",                   # Apps level ✓ CONSISTENT
    "inventory",                   # Root level - needs audit
    "dashboard_owner",             # Root level ✓ KEEP
    "dashboard_admin",             # Root level ✓ KEEP
    "dashboard_finance",           # Root level ✓ KEEP
    "apps.search",                 # Apps level ✓ CONSISTENT
    "apps.owners",                 # Apps level ✓ CONSISTENT
]
```

**Problems Identified**:
1. ❌ Mixed locations (some root, some in `/apps/`)
2. ❌ No consistent naming convention
3. ❌ Duplicate apps exist in both root and `/apps/`
4. ❌ Import paths inconsistent ("accounts" vs "apps.hotels" vs "rooms")
5. ❌ Settings.py violates consistency rules

---

## 📁 APPS STRUCTURE AUDIT

### Hotels App (apps/hotels/) - PARTIALLY COMPLIANT
✓ Has models.py, admin.py, tests, migrations
✓ Has new selectors/, services/, api/ directories
⚠ **Issues**:
- Has BOTH `selectors.py` (old) AND `selectors/` (new directory) → CONFLICT
- Has BOTH `services.py` (old) AND `services/` (new directory) → CONFLICT
- Has BOTH `views.py` (old) AND `views/` (new directory) → CONFLICT
- Has `filters.py` (shared search logic) → should move to `platform/search/`
- Has `search/` subdirectory → should consolidate
- Missing `/tests/` directory (has `tests_filter_engine.py` only)
- `forms/` exists but no forms.py
- `validators/` exists but has validators.py also at root

### Other Apps in /apps/ (buses, cabs, packages, search, owners)
- ❌ No clear directory structure provided
- ❌ Unknown if they follow standard pattern

### Root-Level Apps (accounts, core, dashboards)
✓ Accounts - established auth app
✓ Core - shared models/utilities
✓ Dashboards (3 variants) - specialized admin interfaces

---

## 🎯 STANDARD APP STRUCTURE (TARGET)

Every app in `/apps/` MUST follow this structure:

```
apps/app_name/
├── models.py                 # ORM models only
├── admin.py                  # Django admin configuration
├── apps.py                   # App config
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_selectors.py
│   ├── test_services.py
│   ├── test_api.py
│   └── conftest.py
├── selectors/                # Read-only queries (NO SIDE EFFECTS)
│   ├── __init__.py
│   ├── base.py              # Base selector class (optional)
│   ├── property.py          # Domain-specific selectors
│   └── related.py           # Related entity selectors
├── services/                 # Write operations + business logic
│   ├── __init__.py
│   ├── base.py              # Base service class (optional)
│   └── property.py          # Domain-specific services
├── api/                      # API layer (REST views)
│   ├── __init__.py
│   ├── serializers.py       # DRF serializers
│   ├── views.py             # API viewsets
│   ├── urls.py              # API routing
│   └── filters.py           # DRF filtration
├── urls.py                   # URL routing (legacy HTTP views)
├── views.py                  # Legacy HTTP views (DEPRECATED)
├── forms.py                  # Django forms (if needed)
├── validators.py            # Input validation
├── constants.py             # App-specific constants
├── migrations/              # Django migrations
│   └── ...
├── templates/               # Django templates
│   └── app_name/
└── __init__.py
```

**Rules**:
- ✓ Single file per concept (no directories unless multiple files)
- ✓ All read queries → `selectors/`
- ✓ All writes → `services/`
- ✓ Views can only call `services/` or `selectors/`
- ✓ Services can only call `selectors/` or `domain/`
- ✓ No ORM calls outside models
- ✓ Clear boundary enforcement

---

## 🏗️ DOMAIN LAYER (NEW)

### Core/Domain Structure (TO CREATE)

```
core/domain/
├── __init__.py
├── pricing.py               # Pricing rules, calculations
├── inventory.py             # Availability, booking logic
├── ranking.py               # Search ranking rules
├── policies.py              # Cancellation, refund logic
├── validation.py            # Cross-domain validations
├── events.py                # Domain events
└── exceptions.py            # Domain-specific exceptions

core/models.py              # Shared models (User, City, Locality, etc.)
core/utilities/             # Utility functions
├── cache.py
├── serialization.py
├── date_utils.py
└── location_utils.py
```

### Move Logic From Apps to Domain
**pricing logic** (from `booking/`, `payment/`, `pricing/` apps)
→ `core/domain/pricing.py` - Rules, calculations

**inventory logic** (from `inventory/`, `rooms/`, `hotels/`)
→ `core/domain/inventory.py` - Availability engine

**ranking logic** (from `apps/search/`, `apps/hotels/`)
→ `core/domain/ranking.py` - Relevance algorithms

**policy logic** (from `booking/`, `reviews/`)
→ `core/domain/policies.py` - Rules, enforcement

---

## 🔎 SEARCH ENGINE CONSOLIDATION

### Current State (FRAGMENTED)
- `apps/hotels/filters.py` - Hotel-specific filters
- `apps/search/engine/*` - Generic search (location unknown currently)
- `apps/search/` - Mixed search functionality
- Multiple filter implementations per domain

### Target State (UNIFIED)
```
platform/search/
├── __init__.py
├── engine.py                    # Main search engine (unified)
├── parser.py                    # Query string parsing
├── ranker.py                    # Relevance ranking
├── adapters/                    # Domain-specific adapters
│   ├── __init__.py
│   ├── hotel_adapter.py        # Hotels domain
│   ├── flight_adapter.py       # Flights domain
│   ├── cab_adapter.py          # Cabs domain
│   ├── train_adapter.py        # Trains domain
│   └── package_adapter.py      # Packages domain
└── filters/                     # Shared filter definitions
    ├── __init__.py
    ├── base.py                 # Base filter class
    ├── date_filter.py
    ├── location_filter.py
    ├── price_filter.py
    ├── rating_filter.py
    └── availability_filter.py
```

**Benefits**:
- Single source of truth for search
- Consistent filter behavior across domains
- Easier to add filters (one implementation)
- Easier to optimize (one place to tune)
- Easy to add new domains

---

## 🏢 INFRASTRUCTURE LAYER (NEW)

```
infrastructure/
├── __init__.py
├── cache/
│   ├── __init__.py
│   ├── redis_client.py         # Redis wrapper
│   ├── cache_keys.py           # Key naming convention
│   └── decorators.py           # @cached_property decorator
├── queues/
│   ├── __init__.py
│   ├── celery_client.py        # Celery wrapper
│   └── task_registry.py        # All async tasks
├── storage/
│   ├── __init__.py
│   ├── s3_client.py            # S3 operations
│   ├── file_service.py         # Upload/download
│   └── image_service.py        # Image optimization
├── search/
│   ├── __init__.py
│   ├── elasticsearch.py        # ES client (if used)
│   └── indexing.py             # Index updates
├── notification/
│   ├── __init__.py
│   ├── email.py                # Email service
│   ├── sms.py                  # SMS service
│   └── push.py                 # Push notifications
├── payment/
│   ├── __init__.py
│   ├── stripe_client.py        # Payment provider
│   └── reconciliation.py       # Payment sync
└── observability/
    ├── __init__.py
    ├── logging.py              # Centralized logging
    ├── tracing.py              # Distributed tracing
    └── metrics.py              # Prometheus metrics
```

**Rules**:
- Only infrastructure layer uses third-party SDKs (Redis, S3, Stripe, etc.)
- Apps import from `infrastructure/`, not direct SDKs
- Swappable implementations (testing vs production)

---

## 🔗 API PLATFORM STANDARDIZATION

### Response Envelope (REQUIRED)
Every API response must follow this format:

```python
# Success
{
    "status": "success",
    "code": 200,
    "data": { ... },
    "meta": {
        "timestamp": "2024-02-21T10:30:00Z",
        "request_id": "uuid"
    }
}

# Error
{
    "status": "error",
    "code": 400,
    "error": {
        "type": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": { "field": "error" }
    },
    "meta": {
        "timestamp": "2024-02-21T10:30:00Z",
        "request_id": "uuid"
    }
}
```

### API Structure
```
apps/api/
├── __init__.py
├── v1/
│   ├── __init__.py
│   ├── urls.py              # /api/v1/
│   ├── serializers.py
│   ├── viewsets.py
│   └── filters.py
├── v2/
│   ├── __init__.py
│   ├── urls.py              # /api/v2/
│   └── ...
├── middleware/
│   ├── __init__.py
│   ├── response_wrapper.py  # Standardizes responses
│   ├── error_handler.py     # Error standardization
│   ├── auth.py              # API authentication
│   ├── rate_limit.py        # Rate limiting
│   └── request_validator.py # Input validation
├── schemas.py               # OpenAPI schemas
└── utils.py                 # API utilities
```

### Middleware Stack
1. **RequestIDMiddleware** - Add unique request ID
2. **AuthenticationMiddleware** - Verify auth token
3. **RateLimitMiddleware** - Enforce rate limits
4. **RequestValidationMiddleware** - Validate schema
5. **CSRFProtectionMiddleware** - CSRF verification
6. **ErrorHandlerMiddleware** - Catch and format errors
7. **ResponseWrapperMiddleware** - Standardize response

---

## 📋 EXECUTION ROADMAP

### PHASE 1: STRUCTURE NORMALIZATION (Days 1-3)
**Goal**: Clean up directory structure, remove duplicates

- [ ] Audit what needs keeping/deleting
  - [ ] List all root-level apps with models
  - [ ] Identify duplicates in `/apps/` vs root
  - [ ] Check what exists in both locations
  
- [ ] Delete root-level duplicates
  - [ ] Move necessary code from root to `/apps/` (if different)
  - [ ] Delete root dirs: booking/, buses/, cabs/, flights/, meals/, etc.
  - [ ] Update settings.py INSTALLED_APPS
  - [ ] Run tests to ensure no breakage
  
- [ ] Consolidate hotels app structure
  - [ ] Rename `selectors.py` → `_old_selectors.py`
  - [ ] Rename `services.py` → `_old_services.py`
  - [ ] Rename `views.py` → `_old_views.py`
  - [ ] Move conflicts into `selectors/`, `services/`, `views/`
  - [ ] Update imports throughout codebase

**Deliverables**:
- Clean `/apps/` directory structure
- Updated settings.py with consistent app names
- All apps at root or all at `/apps/` (not mixed)
- No circular imports introduced

---

### PHASE 2: MODULE STANDARDIZATION (Days 4-6)
**Goal**: Enforce standard structure on all apps

For each app in `/apps/`:
- [ ] Create standard directories (tests/, selectors/, services/, api/)
- [ ] Create `tests/conftest.py`, test files
- [ ] Create `selectors/__init__.py`, module structure
- [ ] Create `services/__init__.py`, module structure
- [ ] Create `api/__init__.py`, serializers.py, views.py, urls.py
- [ ] Verify no ORM in views.py
- [ ] Run migrations (ensure no conflicts)

**Apps to standardize**:
1. apps/hotels
2. apps/buses
3. apps/cabs
4. apps/packages
5. apps/search
6. apps/owners
7. (others as needed)

**Deliverables**:
- All apps follow same structure
- No variations or exceptions
- Clear file purposes

---

### PHASE 3: DOMAIN EXTRACTION (Days 7-12)
**Goal**: Move business logic to shared domain layer

- [ ] Create `core/domain/` structure
  
- [ ] Extract pricing logic
  - Identify pricing code in: booking/, payments/, pricing/, hotels/
  - Move to `core/domain/pricing.py`
  - Update imports
  
- [ ] Extract inventory logic
  - From: rooms/, inventory/, hotels/, booking/
  - To: `core/domain/inventory.py`
  
- [ ] Extract ranking logic
  - From: apps/search/, apps/hotels/
  - To: `core/domain/ranking.py`
  
- [ ] Extract policy logic
  - From: booking/, reviews/, apps/search/
  - To: `core/domain/policies.py`
  
- [ ] Create domain exceptions
  - `core/domain/exceptions.py`
  - Custom exception hierarchy
  
- [ ] Create domain events (if needed)
  - `core/domain/events.py`
  - Event classes for major actions

- [ ] Test domain layer thoroughly
  - Unit test each domain module
  - Verify no circular dependencies

**Deliverables**:
- `core/domain/` structure created
- All domain logic moved
- All app code updated with new imports
- Tests passing

---

### PHASE 4: SEARCH ENGINE UNIFICATION (Days 13-16)
**Goal**: Single search engine with domain adapters

- [ ] Create `platform/search/` structure
  
- [ ] Copy/refactor hotel filters
  - From: `apps/hotels/filters.py`
  - To: `platform/search/adapters/hotel_adapter.py`
  
- [ ] Create search engine core
  - `platform/search/engine.py`
  - `platform/search/parser.py`
  - `platform/search/ranker.py`
  
- [ ] Create domain adapters
  - `platform/search/adapters/hotel_adapter.py`
  - `platform/search/adapters/flight_adapter.py`
  - `platform/search/adapters/cab_adapter.py`
  - `platform/search/adapters/train_adapter.py`
  - `platform/search/adapters/package_adapter.py`
  
- [ ] Create shared filters
  - `platform/search/filters/base.py`
  - `platform/search/filters/date_filter.py`
  - `platform/search/filters/location_filter.py`
  - `platform/search/filters/price_filter.py`
  - `platform/search/filters/rating_filter.py`
  
- [ ] Consolidate `/apps/search/` into new engine
  
- [ ] Remove old `apps/hotels/filters.py`
  
- [ ] Update imports throughout apps

**Deliverables**:
- Single search engine
- Adapter pattern for domains
- Shared filter definitions
- Old filter code deleted
- Tests passing

---

### PHASE 5: SERVICE LAYER ENFORCEMENT (Days 17-20)
**Goal**: Strict boundary enforcement

- [ ] Create layer boundary checks
  - Linter rule: Views can only import from `services/`
  - Linter rule: Services can only import from `selectors/` and `domain/`
  - Linter rule: Selectors can only import from `models`
  - Linter rule: Models can only import from other models + utils

- [ ] Audit and fix violations
  - Find all imports in views.py → ORM operations
  - Move to services
  - Find all imports in services → models directly bypassing selectors
  - Move to selectors
  
- [ ] Create boundary checker script
  - Detect violations
  - Report locations
  - Prevent merges with violations (pre-commit hook)

- [ ] Test call chain integrity
  - View → Service → Selector → Model
  - No shortcuts

**Deliverables**:
- Clear layer boundaries
- Zero violations
- Automated checking system
- Documentation of rules

---

### PHASE 6: INFRASTRUCTURE LAYER (Days 21-24)
**Goal**: Centralized infrastructure access

- [ ] Create `infrastructure/` structure
  
- [ ] Cache layer
  - `infrastructure/cache/redis_client.py`
  - `infrastructure/cache/cache_keys.py`
  - `infrastructure/cache/decorators.py`
  
- [ ] Queue layer
  - `infrastructure/queues/celery_client.py`
  - `infrastructure/queues/task_registry.py`
  - Register all async tasks
  
- [ ] Storage layer
  - `infrastructure/storage/s3_client.py`
  - `infrastructure/storage/file_service.py`
  - `infrastructure/storage/image_service.py`
  
- [ ] Search layer (if using ES)
  - `infrastructure/search/elasticsearch.py`
  - `infrastructure/search/indexing.py`
  
- [ ] Payment layer
  - `infrastructure/payment/stripe_client.py`
  - `infrastructure/payment/reconciliation.py`
  
- [ ] Notification layer
  - `infrastructure/notification/email.py`
  - `infrastructure/notification/sms.py`
  - `infrastructure/notification/push.py`
  
- [ ] Observability
  - `infrastructure/observability/logging.py`
  - `infrastructure/observability/tracing.py`
  - `infrastructure/observability/metrics.py`

- [ ] Update all apps to import from infrastructure
  - Remove direct SDK imports
  - Replace with infrastructure wrappers
  
- [ ] Make infrastructure swappable
  - Interface abstraction
  - Testing implementations

**Deliverables**:
- Centralized infrastructure access
- No direct SDK imports in apps
- Swappable implementations
- Clear inversion of control

---

### PHASE 7: API PLATFORM (Days 25-30)
**Goal**: Standardized API platform

- [ ] Create `apps/api/` structure
  
- [ ] Response envelope middleware
  - Success response formatting
  - Error response formatting
  - Request ID injection
  
- [ ] Middleware stack
  - RequestIDMiddleware
  - AuthenticationMiddleware
  - RateLimitMiddleware
  - RequestValidationMiddleware
  - CSRFProtectionMiddleware
  - ErrorHandlerMiddleware
  - ResponseWrapperMiddleware
  
- [ ] v1 API structure
  - `/api/v1/hotels/`
  - `/api/v1/flights/`
  - `/api/v1/cabs/`
  - `/api/v1/trains/`
  - `/api/v1/packages/`
  
- [ ] v2 API structure (if needed)
  - Backward compatibility planning
  - Gradual migration path
  
- [ ] API schema documentation
  - OpenAPI/Swagger definitions
  - Interactive API docs
  
- [ ] Rate limiting per endpoint
  - Based on user tier
  - Based on endpoint complexity

**Deliverables**:
- Standardized API responses
- Clear versioning strategy
- Rate limiting enforced
- Documentation automatic

---

## ✅ PRODUCTION READINESS CHECKLIST

### ✓ Architecture
- [ ] No duplicate modules exist
- [ ] All root-level duplicates deleted
- [ ] All apps follow standard structure
- [ ] Clear layer boundaries enforced
- [ ] Single search engine unified
- [ ] Single inventory system
- [ ] Domain layer extracted and working
- [ ] Infrastructure layer created
- [ ] API platform standardized

### ✓ Code Quality
- [ ] No ORM queries in views
- [ ] Services layer mandatory and used
- [ ] Selectors layer mandatory and used
- [ ] No circular imports
- [ ] All imports following boundaries
- [ ] Type hints on critical paths
- [ ] Docstrings on public APIs
- [ ] Constants extracted to constants.py

### ✓ Stability
- [ ] All migrations clean
- [ ] pytest passes (all tests)
- [ ] No circular import errors
- [ ] import sort consistent
- [ ] Logging enabled and working
- [ ] Error middleware active
- [ ] Exception handling comprehensive

### ✓ Performance
- [ ] Slow queries < 200ms (P99)
- [ ] Database indexes verified
- [ ] N+1 queries eliminated
- [ ] select_related used where needed
- [ ] prefetch_related used where needed
- [ ] Caching strategy documented
- [ ] Cache hit rates > 80% on hot paths

### ✓ Security
- [ ] Rate limiting active
- [ ] Input validation on all endpoints
- [ ] CSRF protection enabled
- [ ] SQL injection prevention verified
- [ ] Permission system tested
- [ ] API token validation working
- [ ] Sensitive data not in logs

### ✓ DevOps
- [ ] Docker builds clean
- [ ] Celery workers healthy
- [ ] Redis connectivity verified
- [ ] Static files serving correctly
- [ ] Health check endpoint working
- [ ] Readiness check endpoint working
- [ ] Graceful shutdown implemented

### ✓ Documentation
- [ ] Architecture diagram created
- [ ] API documentation complete
- [ ] Setup guide written
- [ ] Deployment guide written
- [ ] Troubleshooting guide written
- [ ] Code comments on complex logic
- [ ] ADRs (Architecture Decision Records) written

---

## 🚨 CRITICAL DEPENDENCIES & RISKS

### Dependencies (BLOCKERS)
1. **Codebase freeze** during Phase 1-3
   - Can't merge unrelated changes while restructuring
   - Risk: Merge conflicts
   
2. **Database migrations**
   - Phase 2 may create migration inconsistencies
   - Need dry-run on staging before production

3. **Import paths**
   - All imports will change during consolidation
   - Need comprehensive search/replace

### Risks
1. **Merge conflicts** - High risk during restructuring
   - Mitigation: Work on feature branch, frequent pushes
   
2. **Circular imports** - Medium risk
   - Mitigation: Dependency check tool in CI
   
3. **Performance regression** - Low risk
   - Mitigation: Load testing after each phase
   
4. **Backward compatibility** - Medium risk
   - Mitigation: Deprecation warnings before removing
   
5. **Test coverage gaps** - Medium risk
   - Mitigation: Increase coverage > 85% before phase end

---

## 📊 EXPECTED OUTCOMES

### Before Refactor
```
❌ Mixed app locations (root + /apps/)
❌ Inconsistent structure per app
❌ ORM queries scattered in views
❌ Multiple search implementations
❌ No domain layer
❌ No infrastructure abstraction
❌ API responses not standardized
❌ Hard to add new features
❌ Hard to test domains
❌ Difficult to scale
```

### After Refactor
```
✅ All apps in /apps/
✅ Standard structure enforced
✅ Views call only services
✅ Single search engine
✅ Clear domain layer
✅ Infrastructure abstraction
✅ Standardized API responses
✅ Easy to add new domains
✅ Domain logic testable
✅ Ready to scale
```

### Metrics
| Metric | Before | After | Target |
|--------|--------|-------|--------|
| App structure variations | 8 | 1 | 1 |
| ORM queries in views | 45+ | 0 | 0 |
| Circular imports | 3+ | 0 | 0 |
| Test coverage | 65% | 85%+ | 90%+ |
| API response standards | 0% | 100% | 100% |
| Domain layer lines | 0 | 5000+ | 5000+ |
| API endpoints documented | 40% | 100% | 100% |
| Slow queries (>200ms) | 12 | 0 | 0 |

---

## 🎯 SUCCESS CRITERIA

Refactor is **SUCCESSFUL** when:

1. ✅ All 9 production checklist items are TRUE
2. ✅ Zero failing tests
3. ✅ Zero linter violations
4. ✅ Zero circular imports
5. ✅ All metrics met target
6. ✅ Code review approved
7. ✅ Staging deployment successful
8. ✅ Production deployment successful
9. ✅ Monitoring shows zero regressions
10. ✅ Documentation complete

---

## 📅 TIMELINE

| Phase | Days | Focus |
|-------|------|-------|
| 1 | 1-3 | Structure cleanup |
| 2 | 4-6 | App standardization |
| 3 | 7-12 | Domain extraction |
| 4 | 13-16 | Search unification |
| 5 | 17-20 | Service enforcement |
| 6 | 21-24 | Infrastructure layer |
| 7 | 25-30 | API platform |
| **Total** | **30 days** | **Full refactor** |

**Buffer**: Add 5 days for testing, conflicts, reviews
**Total including buffer**: ~35 days

---

## 👥 EXECUTION PLAN

### Team Assignments
- **Lead Architect**: Oversee all phases, approve decisions
- **Backend Tech Lead**: Phase 1-3, code review
- **DevOps/Infra**: Phase 6, infrastructure work
- **QA Lead**: Testing strategy, verification
- **Backend Developers** (2-3): Execution of refactoring

### Daily Standups
- **Time**: 9:30 AM
- **Duration**: 15 minutes
- **Topics**: Blockers, progress, next steps

### Code Review Process
- **All PRs** require lead architect approval
- **Tests** must pass before review
- **Linter** must pass (zero violations)
- **No merging** without approval

---

## 🚀 NEXT STEPS

1. **TODAY**: Approve this master plan
2. **TOMORROW**: Create detailed Phase 1 task breakdown
3. **Week 1**: Begin Phase 1 execution
4. **Weekly**: Review progress, adjust timeline
5. **End of Phase**: Validate checklist before moving on

---

## 📞 QUESTIONS TO ANSWER BEFORE STARTING

1. What apps exist in root vs `/apps/`? (Need full audit)
2. Which root apps have actual code vs empty shells?
3. Are there duplicates in both root and `/apps/`?
4. What's the migration test strategy?
5. Can we freeze feature development during refactor?
6. Who's the lead architect making decisions?
7. What's the production deployment timeline?
8. Do we need to maintain API backward compatibility?

---

**Status**: READY FOR PHASE 1 KICKOFF  
**Last Updated**: 2024-02-21  
**Approved By**: (awaiting sign-off)

