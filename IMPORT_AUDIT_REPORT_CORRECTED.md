# IMPORT DISCIPLINE ENFORCEMENT - CORRECTED AUDIT & STRATEGY

**Date**: 2026-02-21  
**Status**: PHASE 1 REVISED  
**Corrections Made**: Analyzed actual module structure vs INSTALLED_APPS

---

## CRITICAL DISCOVERY

The actual Django configuration (INSTALLED_APPS in settings.py) reveals:

```python
INSTALLED_APPS = [
    # Root-level apps (NO apps. prefix)
    "accounts",
    "core",
    "rooms",
    "meals",
    "pricing",
    "booking",
    "payments",
    "wallet",
    "promos",
    "reviews",
    "buses",
    "packages",
    "flights",
    "trains",
    "cabs",
    "inventory",
    "dashboard_owner",
    "dashboard_admin",
    "dashboard_finance",
    
    # Under apps/ (WITH apps. prefix)
    "apps.hotels",
    
    # And presumably:
    # "apps.search", "apps.booking", "apps.buses", etc.
]
```

**KEY INSIGHT**: The codebase has a MIXED STRUCTURE:
- Most domain apps are at **ROOT LEVEL** (not under apps/)
- Some newer apps ARE under `apps/`
- Files exist in BOTH locations (duplicate modules)

---

## CORRECTIVE ACTION

The original directive to normalize ALL imports to `apps.*` cannot be fully executed because:
1. Most modules are NOT in `apps/` directory
2. INSTALLED_APPS configuration registers them at root level
3. Moving all modules under `apps/` would require directory restructuring (beyond "normalize imports")

**Revised Strategy**: 

### Normalize ONLY apps that are already under apps/:
- `apps.hotels` → imports should use `from apps.hotels...`
- `apps.search` → imports should use `from apps.search...`
- `apps.cabs` → imports should use `from apps.cabs...`
- `apps.buses` → imports should use `from apps.buses...`
- (and any others actually in apps/)

### LEAVE UNCHANGED (root-level modules):
- `from core...` (core/ is at root, registered as "core")
- `from dashboard_admin...` (dashboard_admin/ is at root)
- `from pricing...` (pricing/ is at root)
- `from inventory...` (inventory/ is at root)
- All other root-level modules

###Current Status:
All changes have been **REVERTED** due to incorrect strategy.

---

## REVISED EXECUTION PLAN

### Phase 1: CORRECT AUDIT (IN PROGRESS)
Identify violations ONLY in apps-level modules

### Phase 2: TARGETED NORMALIZATION
Fix imports in files under `apps/` that reference other `apps/` modules

### Phase 3: VALIDATION
Run `python manage.py check` to verify

### Phase 4: IMPORT GUARD
Create `tools/import_guard.py` to prevent future drift

---

## DELIVERABLES UPDATED

- [x] IMPORT_AUDIT_REPORT.md (ORIGINAL - INVALIDATED DUE TO INCORRECT STRUCTURE ANALYSIS)
- [ ] IMPORT_AUDIT_REPORT_CORRECTED.md (THIS FILE - CORRECTED UNDERSTANDING)
- [ ] IMPORT_FIXES_LOG.md (PENDING - WILL APPLY ONLY to apps/)
- [ ] Final validation report

---

**Next Step**: Clarify actual module structure and execute corrected normalization strategy.
