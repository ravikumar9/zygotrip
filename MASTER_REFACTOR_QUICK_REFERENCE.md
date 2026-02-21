# 🎯 MASTER REFACTOR - QUICK REFERENCE GUIDE

**Purpose**: Fast lookup for architects and developers executing the refactor  
**Status**: Ready to print/post on wall  
**Phases**: 7 phases over 30 days  

---

## 📍 WHERE WE ARE NOW

### Current Problems ❌
```
Mixed app locations      (root + /apps/)
Inconsistent structure   (every app different)
ORM in views            (scattered everywhere)
Multiple search engines (inconsistent, hard to maintain)
No domain layer         (business logic in views/services)
No infrastructure abstraction (third-party SDKs everywhere)
Unstandard APIs         (no response envelope)
Hard to scale           (spaghetti imports, circular deps)
```

### After Refactor ✅
```
All apps in /apps/              (single location)
Standard structure everywhere   (one pattern, all apps)
Views → Services → Selectors   (clean boundaries)
Single search engine           (unified, extensible)
Clear domain layer             (reusable logic)
Infrastructure abstraction     (swappable implementations)
Standardized API responses     (envelope + versioning)
Scale-ready architecture       (clean, testable, modular)
```

---

## 📅 THE 7 PHASES

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: Structure Normalization (Days 1-3)                   │
│ → Delete root app duplicates                                  │
│ → Consolidate /apps/                                          │
│ → Update imports, fix settings.py                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: Module Standardization (Days 4-6)                    │
│ → Enforce standard structure on all apps                      │
│ → Create tests/, selectors/, services/, api/ directories      │
│ → Move/organize code by responsibility                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: Domain Extraction (Days 7-12)                        │
│ → Create core/domain/ layer                                   │
│ → Move pricing → core/domain/pricing.py                       │
│ → Move inventory → core/domain/inventory.py                   │
│ → Move ranking → core/domain/ranking.py                       │
│ → Move policies → core/domain/policies.py                     │
│ → Shared, testable business logic                             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: Search Unification (Days 13-16)                      │
│ → Create platform/search/ engine                              │
│ → Move apps/hotels/filters.py → adapter                       │
│ → Single search engine + domain adapters                      │
│ → Replace all app-specific search implementations             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: Service Enforcement (Days 17-20)                     │
│ → Strict layer boundary checks                                │
│ → Views only call services                                    │
│ → Services only call selectors + domain                       │
│ → Selectors only call models                                  │
│ → Detect and fix violations                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 6: Infrastructure Layer (Days 21-24)                    │
│ → Create infrastructure/ wrapper layer                        │
│ → Move redis logic → infrastructure/cache/                    │
│ → Move celery → infrastructure/queues/                        │
│ → Move file storage → infrastructure/storage/                 │
│ → Move payment SDKs → infrastructure/payment/                 │
│ → Single point of external service access                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 7: API Platform (Days 25-30)                            │
│ → Standardize all API responses                               │
│ → Response envelope middleware                                │
│ → Error standardization                                       │
│ → API versioning (/api/v1/, /api/v2/)                         │
│ → Rate limiting + auth                                        │
│ → API documentation                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 PHASE 1 - WHAT TO DELETE

| What | Where | Status | Action |
|------|-------|--------|--------|
| accounts/ | root | KEEP - unique | Don't touch |
| booking/ | root | DELETE | Move to /apps/booking/ |
| buses/ | root | DELETE | Already in apps/buses/ |
| cabs/ | root | DELETE | Empty, apps/cabs/ exists |
| dashboard_admin/ | root | KEEP - special | Don't touch |
| dashboard_finance/ | root | KEEP - special | Don't touch |
| dashboard_owner/ | root | KEEP - special | Don't touch |
| flights/ | root | DELETE | Move to /apps/flights/ |
| meals/ | root | DELETE | Move to /apps/meals/ |
| payments/ | root | DELETE | Move to /apps/payments/ |
| pricing/ | root | DELETE | Move to /apps/pricing/ |
| promos/ | root | DELETE | Move to /apps/promos/ |
| reviews/ | root | DELETE | Move to /apps/reviews/ |
| rooms/ | root | DELETE | Move to /apps/rooms/ |
| trains/ | root | DELETE | Move to /apps/trains/ |
| wallet/ | root | DELETE | Move to /apps/wallet/ |
| registration/ | root | DELETE | Deprecated |

---

## 🔧 STANDARD APP STRUCTURE

**Every app MUST follow this:**

```
apps/app_name/
├── models.py           # ORM only
├── admin.py            # Django admin
├── apps.py            # Config
│
├── selectors/          # Read queries
│   ├── __init__.py
│   └── queries.py
│
├── services/           # Write + logic
│   ├── __init__.py
│   └── operations.py
│
├── api/                # REST API
│   ├── __init__.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── tests/              # Tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_selectors.py
│   ├── test_services.py
│   └── test_api.py
│
├── migrations/         # Database
├── urls.py             # URL routing
├── forms.py            # Django forms
├── validators.py       # Input checks
├── constants.py        # Constants
└── __init__.py
```

---

## 📋 LAYER BOUNDARIES (STRICT)

```
┌─────────────────────────────────────────────────────────────┐
│ VIEWS / VIEWSETS                                            │
│ ✓ Can call: services/                                      │
│ ✗ Cannot call: models, selectors (except through services) │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────┐
│ SERVICES                                                    │
│ ✓ Can call: selectors/, domain/                            │
│ ✗ Cannot call: models directly                             │
└────────────────┬────────────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
┌──────────────┐   ┌─────────────────────┐
│ SELECTORS    │   │ DOMAIN LOGIC        │
│ ============ │   │ =================== │
│ Read-only    │   │ Pricing rules       │
│ No side fx   │   │ Inventory logic     │
│ Can call:    │   │ Ranking/sorting     │
│  - models    │   │ Policy enforcement  │
└──────┬───────┘   └──────────┬──────────┘
       │                      │
       └──────────┬───────────┘
                  ▼
          ┌───────────────┐
          │ MODELS/ORM    │
          │ ============= │
          │ Database      │
          │ No logic here │
          └───────────────┘
```

---

## 💾 DOMAIN LAYER STRUCTURE

```
core/domain/
├── pricing.py          # Price calculations, rules
├── inventory.py        # Availability, bookings
├── ranking.py         # Search ranking algorithms
├── policies.py        # Refund, cancellation logic
├── validation.py      # Cross-domain checks
├── events.py          # Domain events (optional)
└── exceptions.py      # Custom exceptions
```

**Rule**: Testable, reusable business logic that multiple apps need

---

## 🔍 SEARCH ENGINE UNIFICATION

**Before** (FRAGMENTED):
```
apps/hotels/filters.py          ← Hotel filters only
apps/search/engine/             ← Generic search (mixed)
apps/cabs/search/               ← Cab filters (separate)
apps/flights/search/            ← Flight filters (separate)
Multiple implementations, hard to maintain
```

**After** (UNIFIED):
```
platform/search/
├── engine.py                   ← Single search engine
├── parser.py                   ← Query string parsing
├── ranker.py                   ← Ranking algorithm
└── adapters/                   ← Domain-specific adapters
    ├── hotel_adapter.py        ← Hotels-specific filters
    ├── flight_adapter.py       ← Flights-specific filters
    ├── cab_adapter.py          ← Cabs-specific filters
    ├── train_adapter.py        ← Trains-specific filters
    └── package_adapter.py      ← Packages-specific filters

Single source of truth, easy to maintain, add new domains
```

---

## 🏢 INFRASTRUCTURE LAYER

**Before** (SCATTERED):
```
apps/hotels/        import redis       ← Direct SDK
apps/booking/       import celery      ← Direct SDK
apps/payments/      import stripe      ← Direct SDK
apps/rooms/         import boto3       ← Direct SDK
Hard to test, hard to swap providers
```

**After** (ABSTRACTED):
```
infrastructure/
├── cache/redis_client.py       ← All redis logic
├── queues/celery_client.py     ← All celery logic
├── payment/stripe_client.py    ← All payment logic
├── storage/s3_client.py        ← All file storage logic

Apps import from infrastructure/, not direct SDKs
Easy to test, easy to swap providers
```

---

## 🌐 API STANDARDIZATION

**Response Envelope** (REQUIRED):

```json
{
  "status": "success|error",
  "code": 200,
  "data": { "hotels": [...] },
  "meta": {
    "timestamp": "2024-02-21T...",
    "request_id": "uuid"
  }
}
```

**Versioning**:
```
/api/v1/hotels/      ← Current version
/api/v2/hotels/      ← Future version
Always include version in URL
```

**Middleware Stack**:
```
Request
  ↓
RequestIDMiddleware        (add request_id)
  ↓
AuthenticationMiddleware   (verify token)
  ↓
RateLimitMiddleware        (check quotas)
  ↓
RequestValidationMiddleware (validate schema)
  ↓
CSRFProtectionMiddleware   (CSRF check)
  ↓
View/Viewset
  ↓
ErrorHandlerMiddleware     (catch errors)
  ↓
ResponseWrapperMiddleware  (standardize response)
  ↓
Response
```

---

## ✅ PRODUCTION READINESS CHECKLIST

### Architecture
- [ ] No duplicate modules
- [ ] All apps follow standard structure
- [ ] Clear layer boundaries
- [ ] Single search engine
- [ ] Domain layer working
- [ ] Infrastructure abstracted

### Code Quality
- [ ] No ORM in views
- [ ] Services layer used
- [ ] Selectors layer used
- [ ] No circular imports
- [ ] Type hints present
- [ ] Docstrings present

### Testing
- [ ] All tests pass
- [ ] 90%+ coverage
- [ ] Migrations clean
- [ ] No import errors

### Performance
- [ ] Queries < 200ms P99
- [ ] Indexes verified
- [ ] N+1 removed
- [ ] Caching working

### Security
- [ ] Rate limiting
- [ ] Input validation
- [ ] CSRF protection
- [ ] Auth working

### DevOps
- [ ] Docker builds
- [ ] Celery works
- [ ] Redis works
- [ ] Healthchecks

---

## 🎯 THIS WEEK'S FOCUS

### Days 1-3: PHASE 1
- [ ] Audit apps (what's root, what's /apps/)
- [ ] Delete duplicates
- [ ] Update settings.py
- [ ] Fix imports
- [ ] All tests pass

### Deliverable
- Clean directory structure
- No duplicates
- All imports working
- Settings consistent

---

## 📚 DOCUMENTATION PROVIDED

1. **MASTER_REFACTOR_EXECUTION_PLAN.md**
   - Complete 30-day roadmap
   - All 7 phases detailed
   - Risks, timeline, checklist
   - Read this for overview

2. **PHASE_1_DETAILED_EXECUTION.md**
   - Step-by-step Phase 1 guide
   - Code snippets for each step
   - What to delete, what to keep
   - Import fixing strategies
   - Read this to execute Phase 1

3. **QUICK_REFERENCE_GUIDE.md** (this document)
   - Visual quick lookups
   - Checklists and tables
   - Keep on your desk
   - Print and post on wall

---

## 🆘 QUICK TROUBLESHOOTING

### Problem: ImportError after changes
**Solution**: 
1. Verify INSTALLED_APPS in settings.py
2. Check __init__.py files exist
3. Verify file was moved, not deleted
4. Test imports: `python manage.py shell`

### Problem: Migrations failing
**Solution**:
1. Check for duplicate models
2. Verify no new migrations were auto-created
3. Try: `python manage.py migrate --fake-initial`
4. Last resort: delete migration, re-create

### Problem: Tests failing
**Solution**:
1. Check import paths
2. Run individual tests: `pytest app/tests/test_x.py`
3. Check for wrong test fixtures
4. Verify test database is clean

### Problem: Circular imports
**Solution**:
1. Find cycle: `python -c "import app"`
2. Break cycle by moving to different layer
3. Use late imports inside functions (temporary)
4. Refactor to respect boundaries

---

## 📞 WHO TO ASK

| Question | Ask |
|----------|-----|
| Architecture decisions? | Lead Architect |
| Code structure questions? | Tech Lead |
| Infrastructure changes? | DevOps Lead |
| Test strategy? | QA Lead |
| Import errors? | Whoever wrote that code |
| Timeline questions? | Project Manager |

---

## 🚀 SUCCESS METRICS

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| App structure variations | 8 | 1 | 1✓ |
| ORM queries in views | 45+ | 0 | 0✓ |
| Circular imports | 3+ | 0 | 0✓ |
| Test coverage | 65% | 85%+ | 90%+✓ |
| Slow queries (>200ms) | 12 | 0 | 0✓ |
| API standardization | 0% | 100% | 100%✓ |

---

## ⏱️ TIME ESTIMATES

| Phase | Days | Dev Time | QA Time | Total |
|-------|------|----------|---------|-------|
| 1 | 1-3 | 20h | 5h | 25h |
| 2 | 4-6 | 18h | 4h | 22h |
| 3 | 7-12 | 30h | 8h | 38h |
| 4 | 13-16 | 25h | 6h | 31h |
| 5 | 17-20 | 20h | 5h | 25h |
| 6 | 21-24 | 22h | 5h | 27h |
| 7 | 25-30 | 25h | 8h | 33h |
| **Total** | **30** | **160h** | **41h** | **201h** |

**Team Size**: 3 developers = ~67 hours each
**Timeline**: 4-5 weeks full-time

---

## 🎯 NEXT STEP

1. **Review** MASTER_REFACTOR_EXECUTION_PLAN.md (big picture)
2. **Print** this QUICK_REFERENCE_GUIDE.md
3. **Read** PHASE_1_DETAILED_EXECUTION.md
4. **Start** Phase 1 tomorrow
5. **Daily standup** 9:30 AM
6. **Weekly review** Friday 5 PM

---

**Let's build a production-grade architecture! 🚀**

Last updated: 2024-02-21  
Status: Ready to execute Phase 1

