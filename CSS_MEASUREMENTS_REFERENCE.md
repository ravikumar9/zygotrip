# ZygoTrip CSS Implementation - Exact Measurements Reference

## 🎯 OTA-Grade Visual Specifications (All Verified ✅)

### Header (Topbar)
```css
.topbar {
  height: 64px;                    /* ✅ OTA Spec */
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  padding: 0;                      /* Content height from flex */
  position: sticky;
  top: 0;
  z-index: 100;
}

.topbar .container {
  display: flex;
  align-items: center;             /* Vertically center all content */
  justify-content: space-between;
  width: 100%;
  padding: 0 var(--space-4);      /* 16px horizontal padding */
}

.topbar nav {
  display: flex;
  gap: 32px;                       /* Navigation link spacing */
  align-items: center;
  justify-content: center;         /* Center nav items */
  flex: 1;                         /* Takes remaining space */
}

.topbar .auth-buttons {
  display: flex;
  gap: 12px;                       /* Button spacing */
  align-items: center;
}

.topbar .auth-buttons .btn {
  height: 40px;                    /* Slightly smaller in header */
  padding: 0 16px;                 /* 0 20px in full button */
  font-size: 14px;                 /* Small text in header */
  line-height: 40px;               /* Vertical center */
}
```

### Button System
```css
.btn {
  display: inline-block;
  height: 44px;                    /* ✅ OTA SPEC - Exact 44px */
  padding: 0 20px;                 /* ✅ OTA SPEC - Exact 0 20px */
  border-radius: 8px;              /* ✅ OTA SPEC - Exact 8px */
  font-size: 15px;                 /* var(--text-body) */
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  line-height: 44px;               /* Vertically center text */
  vertical-align: middle;
  white-space: nowrap;
}

.btn-primary {
  background: var(--primary);      /* #ff6b35 */
  color: var(--card);              /* #ffffff */
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(90deg, var(--primary), var(--secondary));
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(255, 107, 53, 0.3);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-secondary {
  background: var(--secondary);    /* #1e3c72 */
  color: var(--card);              /* #ffffff */
}

.btn-secondary:hover:not(:disabled) {
  background: var(--accent);       /* #2a5298 */
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(30, 60, 114, 0.2);
}

.btn-ghost {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text);
}

.btn-ghost:hover:not(:disabled) {
  background: var(--bg);
  border-color: var(--primary);
  color: var(--primary);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn.w-full {
  width: 100%;
}
```

### Form Input System
```css
input[type="text"],
input[type="email"],
input[type="password"],
input[type="search"],
input[type="date"],
input[type="number"],
textarea,
select {
  width: 100%;
  height: 44px;                    /* ✅ OTA SPEC - Exact 44px */
  padding: 0 14px;                 /* ✅ OTA SPEC - Exact 0 14px */
  border: 1px solid #e2e8f0;
  border-radius: 8px;              /* ✅ OTA SPEC - Exact 8px */
  font-size: 15px;                 /* var(--text-body) */
  font-family: var(--font-family);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  background: var(--card);         /* #ffffff */
  color: var(--text);              /* #111827 */
}

input[type="text"]::placeholder,
input[type="email"]::placeholder,
input[type="password"]::placeholder,
input[type="search"]::placeholder,
input[type="date"]::placeholder,
input[type="number"]::placeholder,
textarea::placeholder {
  color: var(--muted);             /* #6b7280 */
}

input[type="text"]:focus,
input[type="email"]:focus,
input[type="password"]:focus,
input[type="search"]:focus,
input[type="date"]:focus,
input[type="number"]:focus,
textarea:focus,
select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.15); /* ✅ OTA SPEC */
}

textarea {
  height: auto;
  min-height: 100px;
  padding: 12px 14px;
  resize: vertical;
}

select {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}
```

### Card System
```css
.card {
  background: var(--card);         /* #ffffff */
  border-radius: 12px;             /* ✅ OTA SPEC - Exact 12px */
  box-shadow: 0 4px 12px rgba(0,0,0,.06); /* ✅ OTA SPEC */
  padding: 20px;                   /* ✅ OTA SPEC - Exact 20px */
  border: 1px solid var(--border); /* #e5e7eb */
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
}
```

### Hotel Card Component
```css
.hotel-card {
  background: var(--card);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,.06);
  border: 1px solid var(--border);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.hotel-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0,0,0,.12);
}

.hotel-card .image-wrapper {
  width: 100%;
  height: 200px;                   /* Standard card image height */
  background: var(--bg);
  overflow: hidden;
  position: relative;
}

.hotel-card .image-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hotel-card .content {
  padding: 20px;                   /* Same as card padding */
  display: flex;
  flex-direction: column;
  flex: 1;
}

.hotel-card .title {
  font-size: 16px;                 /* Body + 1px */
  font-weight: 600;
  margin: 0 0 8px 0;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hotel-card .rating-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
}

.hotel-card .stars {
  color: #ffb800;                  /* Star rating color */
  font-weight: 600;
}

.hotel-card .reviews {
  color: var(--muted);             /* #6b7280 */
  font-size: 13px;
}

.hotel-card .description {
  font-size: 13px;
  color: var(--muted);
  margin-bottom: 12px;
  line-height: 1.4;
  flex: 1;
}

.hotel-card .price-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  margin-top: auto;
}

.hotel-card .price {
  font-size: 24px;                 /* Prominent price */
  font-weight: 700;
  color: var(--primary);           /* #ff6b35 */
}

.hotel-card .discount {
  background: var(--primary);
  color: var(--card);
  font-size: 12px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 6px;              /* Smaller radius for badge */
}
```

### Searchbox Component
```css
.searchbox {
  background: var(--card);
  padding: 24px;                   /* var(--space-6) */
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,.08);
  border: 1px solid var(--border);
}

.searchbox form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;                       /* var(--space-4) */
  align-items: end;
}

.searchbox .form-group {
  position: relative;
  display: flex;
  flex-direction: column;
}

.searchbox label {
  display: block;
  font-size: 13px;                 /* var(--text-small) */
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.searchbox input,
.searchbox select {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 15px;
}

.searchbox input:focus,
.searchbox select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(255, 107, 53, 0.15);
}

.searchbox .btn {
  width: 100%;
}
```

### Autocomplete Dropdown
```css
.autocomplete-results {
  position: absolute;              /* ✅ OTA SPEC */
  top: 100%;                       /* Directly below input */
  left: 0;                         /* Align with input */
  right: 0;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0,0,0,.12);
  max-height: 300px;
  overflow-y: auto;
  z-index: 1000;                   /* ✅ OTA SPEC - Above all */
  margin-top: 4px;
  width: 100%;                     /* ✅ OTA SPEC */
}

.autocomplete-results.hidden {
  display: none;
}

.autocomplete-results .suggestion-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
  transition: background 0.1s ease;
}

.autocomplete-results .suggestion-item:last-child {
  border-bottom: none;
}

.autocomplete-results .suggestion-item:hover {
  background: var(--bg);
  color: var(--primary);
}
```

### Filters Sidebar
```css
.filters {
  position: sticky;
  top: 80px;                       /* Below header */
  width: 280px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
}

.filter-section {
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}

.filter-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.filter-section h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 16px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text);
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.filter-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  margin: 0;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: var(--primary);
}

.filter-count {
  color: var(--muted);
  font-size: 13px;
  margin-left: auto;
}
```

### Pagination
```css
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: var(--space-8);      /* 32px */
  padding-top: var(--space-8);
  border-top: 1px solid var(--border);
}

.pagination a,
.pagination span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 8px;
  font-size: 14px;
  text-decoration: none;
  border: 1px solid var(--border);
  color: var(--text);
  transition: all 0.2s ease;
}

.pagination a:hover {
  border-color: var(--primary);
  color: var(--primary);
  background: rgba(255, 107, 53, 0.05);
}

.pagination .current {
  background: var(--primary);
  color: var(--card);
  border-color: var(--primary);
  font-weight: 600;
}
```

### Grid Layout System
```css
.grid {
  display: grid;
  gap: var(--space-6);            /* 24px */
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-6);
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

.grid-4 {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-6);
}

.sidebar-layout {
  display: grid;
  grid-template-columns: 280px 1fr;  /* Fixed sidebar + flexible content */
  gap: var(--space-6);
}
```

### Responsive Breakpoints
```css
@media (max-width: 1024px) {
  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
  }

  .sidebar-layout {
    grid-template-columns: 220px 1fr;
  }

  .filters {
    position: static;
    width: 100%;
    max-height: none;
    margin-bottom: var(--space-6);
  }
}

@media (max-width: 768px) {
  .grid-3,
  .grid-2,
  .grid-4 {
    grid-template-columns: 1fr;
  }

  .sidebar-layout {
    grid-template-columns: 1fr;
  }

  .topbar nav {
    flex-direction: column;
    gap: var(--space-4);
  }

  .searchbox form {
    grid-template-columns: 1fr;
  }

  h1 {
    font-size: 24px;
  }

  h2 {
    font-size: 20px;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 var(--space-3);      /* 12px */
  }

  .topbar .logo {
    font-size: 18px;
  }

  .searchbox {
    padding: var(--space-4);        /* 16px */
  }

  .pagination a,
  .pagination span {
    width: 32px;
    height: 32px;
    font-size: 12px;
  }
}
```

---

## Summary of Measurements

| Component | CSS Property | OTA Value | Status |
|-----------|--------------|-----------|--------|
| Header | height | 64px | ✅ |
| Button | height | 44px | ✅ |
| Button | padding | 0 20px | ✅ |
| Button | border-radius | 8px | ✅ |
| Input | height | 44px | ✅ |
| Input | padding | 0 14px | ✅ |
| Input | border-radius | 8px | ✅ |
| Input Focus | box-shadow | 0 0 0 3px rgba(...) | ✅ |
| Card | padding | 20px | ✅ |
| Card | border-radius | 12px | ✅ |
| Card | box-shadow | 0 4px 12px rgba(...) | ✅ |
| Radius sm | value | 8px | ✅ |
| Radius md | value | 12px | ✅ |
| Radius lg | value | 16px | ✅ |
| Grid desktop | columns | 3 | ✅ |
| Grid tablet | columns | 2 | ✅ |
| Grid mobile | columns | 1 | ✅ |

**All OTA specifications implemented and verified. ✅**
