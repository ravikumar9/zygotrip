# PRODUCTION-GRADE REPAIR FIX PLAN
## Zygotrip OTA — Hard Mode Execution

**Audit Date**: Feb 20, 2026  
**Risk Level**: HIGH  
**Estimated Effort**: 24-30 hours of automated repair

---

## EXECUTIVE SUMMARY

**9 Critical Issues Found** across template hierarchy, CSS system, component duplication, and search architecture. This plan prioritizes root-cause structural repairs over patch-based fixes.

---

## CRITICAL ISSUES & ROOT CAUSES

| Issue | Root Cause | Impact | Fix Category |
|-------|-----------|--------|--------------|
| Duplicate list.html | Templates in 2 locations | Inconsistent hotel display | Phase 2 - Template Authority |
| 5 Search implementations | No search authority | Autocomplete/results broken | Phase 5 - Search Consolidation |
| 4 Card variants | No component standard | Visual inconsistency | Phase 4 - Component Rebuild |
| 6 CSS files | No CSS authority | Style conflicts, bloat | Phase 3 - CSS System |
| Duplicate search bars | Copy-paste errors | Maintenance nightmare | Phase 4 - Component Removal |
| 8 Unused components | No pruning process | Technical debt | Phase 4 - Component Cleanup |
| Broken component paths | Comments remain after moves | Confusion, broken includes | Phase 4 - Cleanup |
| No layout hierarchy | Every page defines own layout | Inconsistent spacing/structure | Phase 2 - Base Layout |
| Broken footer placement | Inline positioning | Footer floats mid-page | Phase 7 - Footer Fix |

---

## PHASE-BY-PHASE FIX PLAN

### **PHASE 2: LAYOUT AUTHORITY SYSTEM** (2 hours)

**Goal**: Enforce `base.html` as ONLY layout authority

**Changes**:
1. ✅ Update `templates/base.html` to include:
   - Site header (responsive, sticky)
   - Site footer (full-width, bottom-aligned)
   - Main container with proper grid
   - Viewport/meta tags
   - CSS includes (ONLY tokens.css + ui.css)

2. **Delete**:
   - `templates/layouts/` (all custom layout templates)
   - Any page that redefines `<html>` or `<body>`

3. **Update all pages** to use:
   ```django
   {% extends "base.html" %}
   {% block content %}...{% endblock %}
   ```

---

### **PHASE 3: CSS SYSTEM REBUILD** (3 hours)

**Goal**: Single CSS system (tokens.css + ui.css only)

**Current State**:
- `static/css/tokens.css` ✅ (good - design tokens)
- `static/css/ui.css` ✅ (exists but incomplete)
- `static/css/base.css` ❌ (delete - redundant)
- `static/css/components.css` ❌ (delete - redundant)
- `static/css/layout.css` ❌ (delete - redundant)
- `static/css/ota-ui.css` ❌ (delete - legacy)

**Actions**:
1. **Consolidate** components.css → ui.css
2. **Consolidate** layout.css → ui.css  
3. **Consolidate** ota-ui.css → ui.css
4. **Delete** old CSS files
5. **Audit** ui.css for:
   - Grid system (3/2/1 columns) ✅
   - Flex utilities ✅
   - Card styles ✅
   - Form styles ✅
   - Button states ✅
   - Responsive queries ✅

---

### **PHASE 4: COMPONENT STANDARDIZATION** (6 hours)

**Goal**: Replace all UI chaos with reusable components

**Required Components** (canonical):
```
templates/components/
  ├── header.html (navbar, sticky)
  ├── footer.html (dark, 4-col grid)
  ├── container.html (wrapper with padding/max-width)
  ├── section.html (h2 + content wrapper)
  ├── card.html (generic white card)
  ├── hotel_card.html (image/title/location/rating/price/cta)
  ├── search_bar.html (unified search input)
  ├── filter_sidebar.html (unified filters)
  ├── empty_state.html (no results)
  ├── error_state.html (error display)
  ├── loading_state.html (skeleton/spinner)
  └── pagination.html (pagination links)

templates/layouts/
  └── DELETE ALL (use base.html only)

templates/partials/
  └── DELETE/MERGE (move to components/)
```

**Deletions**:
- `templates/components/enhanced_hotel_card.html` (use hotel_card.html)
- `templates/components/listing_card.html` (use hotel_card.html)
- `templates/components/hotel_card_list.html` (use hotel_card.html)
- `templates/partials/enhanced_search_bar.html` (use search_bar.html)
- `templates/components/enhanced_search_bar.html` (use search_bar.html)
- `templates/partials/destination_cards.html` (use card.html in loop)
- `templates/components/destination_cards.html` (use card.html in loop)
- All unused state components (implement in error_state.html, empty_state.html)

**Consolidations**:
- `apps/hotels/templates/hotels/list.html` → DELETE (use templates/hotels/list.html)
- Price block variants → single `price_block.html`

---

### **PHASE 5: SEARCH SYSTEM FIX** (4 hours)

**Goal**: Single search authority with working autocomplete + results

**Authority**: `apps/search/engine.py` (UnifiedSearchEngine)

**Delete**:
- Duplicate search in `apps/hotels/api/v1/views.py` (keep only basic property search)
- Any custom search logic in buses/packages/cabs apps
- `apps/search/services/` (if it exists)

**Enforce**:
- `/search/` → search_list view (HTML results page)
- `/search/autocomplete/` → autocomplete API (JSON)
- Single template: `templates/search/list.html`

**Autocomplete behavior** (must implement):
- Trigger after 2 characters
- Call `/search/autocomplete/?q=...`
- Show dropdown (cities/hotels/localities)
- Keyboard navigation (arrow keys, enter)
- Click to select
- Enter to submit search

**Results page** (must show state):
- Loading → spinner
- Empty → empty state component
- Error → error state component
- Results → hotel cards in 3-col grid

---

### **PHASE 6: HOTEL LIST UI REBUILD** (3 hours)

**Goal**: Responsive, equal-height hotel cards with all required info

**Card Layout**:
```
┌─────────────────────┐
│   Image (4:3)       │
├─────────────────────┤
│ Title               │
│ Location (gray)     │
│ ⭐⭐⭐⭐ 4.2 (10)    │
├─────────────────────┤
│ Amenities: WiFi • Pool
├─────────────────────┤
│ Price: ₹2,500       │
│ [View Details →]    │
└─────────────────────┘
```

**Responsive Grid**:
- Desktop (1024px+): 3 columns
- Tablet (768px-1023px): 2 columns
- Mobile (<768px): 1 column

**Implementation**:
- Use `hotel_card.html` component
- Loop in `templates/hotels/list.html`
- Grid CSS in ui.css
- All cards equal height (flex column)

---

### **PHASE 7: HEADER + FOOTER FIX** (2 hours)

**Goal**: Sticky header, proper footer (never floats)

**Header (`components/header.html`)**:
- Position: fixed / sticky
- z-index: 1000
- Full width
- Center aligned nav
- Responsive: hamburger menu on mobile
- Padding: top site-main by 72px

**Footer (`components/footer.html`)**:
- Position: relative (NOT fixed)
- Full width
- Dark background (#1f2937 or from tokens)
- 4 column grid (About | Links | Contact | Social)
- Copyright centered below
- Never overlaps content

**Fix base.html**:
```html
<body class="site-body">
  {% include "components/header.html" %}
  <main class="site-main">
    {% block content %}{% endblock %}
  </main>
  {% include "components/footer.html" %}
</body>
```

---

### **PHASE 8: GOOGLE MAPS FIX** (1 hour)

**Goal**: Maps render only if API key exists, else show static placeholder

**Implementation**:
```django
{% if google_maps_api_key %}
  <iframe src="https://www.google.com/maps/embed?pb=..." width="100%" height="400"></iframe>
{% else %}
  <div class="bg-gray-200 h-96 flex items-center justify-center">
    <p>Interactive map not available</p>
  </div>
{% endif %}
```

**Check**: `settings.GOOGLE_MAPS_API_KEY` handling

---

### **PHASE 9: OWNER DASHBOARDS** (4 hours)

**Goal**: All properties creatable via UI-only forms (no seed scripts)

**Forms Required**:
1. Add Hotel (dashboard_owner/templates/add_property.html)
2. Add Room (dashboard_owner/templates/add_room.html)
3. Add Bus (dashboard_owner/templates/add_bus.html)
4. Add Cab (dashboard_owner/templates/add_cab.html)
5. Add Package (dashboard_owner/templates/add_package.html)

**Each form must**:
- Save to database
- Appear in owner property listing
- Auto-redirect to listing view
- Show success message
- Handle validation errors

**Implementation**:
- Use Django model forms
- Create standard form template blocks
- Ensure all fields required/optional per model

---

### **PHASE 10: FINAL VALIDATION** (1 hour)

**Run**:
1. `python manage.py check` (0 errors)
2. `python manage.py migrate` (apply any pending)
3. Template validation (no missing includes)
4. CSS class scan (all classes in ui.css)
5. URL validation (no broken URLs)
6. Visual inspection (screenshots of key pages)

---

## EXECUTION SEQUENCE

```
Phase 2 (Layout)          → 2 hours
Phase 3 (CSS)             → 3 hours
Phase 4 (Components)      → 6 hours
Phase 5 (Search)          → 4 hours
Phase 6 (Hotel List)      → 3 hours
Phase 7 (Header/Footer)   → 2 hours
Phase 8 (Maps)            → 1 hour
Phase 9 (Dashboards)      → 4 hours
Phase 10 (Validation)     → 1 hour
─────────────────────────────────
TOTAL: 26 hours automated repair
```

---

## SUCCESS CRITERIA

✅ All pages use base.html layout  
✅ All CSS from (tokens.css + ui.css) only  
✅ No duplicate components  
✅ Search autocomplete works (2+ chars)  
✅ Hotel cards responsive (3/2/1 cols)  
✅ Header sticky, footer at bottom  
✅ Maps conditional (API key check)  
✅ Owner forms create properties  
✅ Django check: 0 errors  
✅ All URLs working (200/302 responses)  
✅ Visual consistency across all pages  

---

## FILES TO MODIFY

| Phase | Type | Count | Files |
|-------|------|-------|-------|
| 2 | Templates | 8 | base.html + layouts/* |
| 3 | CSS | 2 | ui.css (merge), delete 4 |
| 4 | Components | 20 | Create 12, delete 8 |
| 5 | Search | 5 | Consolidate search logic |
| 6 | Hotels | 3 | Fix list.html, grid, card |
| 7 | Header/Footer | 3 | Create/fix components |
| 8 | Maps | 2 | Fix detail pages |
| 9 | Dashboards | 5 | Fix forms |
| 10 | Config | 1 | settings.py validation |
| | **TOTAL** | **49** | |

---

## EXPECTED OUTPUTS

1. ✅ File manifest (files modified/deleted/created)
2. ✅ System rebuild summary (what changed)
3. ✅ Visual improvement list
4. ✅ Risk assessment
5. ✅ Go-live readiness checklist

---

**START DATE**: Feb 20, 2026  
**STATUS**: Ready for Phase 2 Execution  
**APPROVAL**: All 9 critical issues will be fixed. No partial patches.
