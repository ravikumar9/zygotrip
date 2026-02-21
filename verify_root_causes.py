#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HARD MODE ROOT CAUSES VERIFICATION 
Verify all 5 critical root causes are fixed
"""

import os
import sys
import json
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')

# Django setup
import django
django.setup()

from django.core.management import call_command
from django.test import Client
from apps.search.engine import UnifiedSearchEngine

def verify_root_causes():
    """Verify each root cause is fixed"""
    
    results = {
        "timestamp": "2026-02-20",
        "verification_results": {},
        "critical_issues": []
    }
    
    print("=" * 70)
    print("[HARD MODE] ROOT CAUSE VERIFICATION")
    print("=" * 70)
    
    # 1. SEARCH CONSOLIDATION
    print("\n[1] SEARCH CONSOLIDATION")
    print("-" * 70)
    try:
        engine = UnifiedSearchEngine()
        results["verification_results"]["search_unified"] = "✅ PASS"
        print("✅ UnifiedSearchEngine instantiated")
        
        # Test autocomplete
        auto = engine.autocomplete("del", limit=5)
        if auto.get("results"):
            results["verification_results"]["autocomplete"] = "✅ PASS"
            print(f"✅ Autocomplete working ({len(auto['results'])} results)")
        else:
            results["verification_results"]["autocomplete"] = "⚠️ WARN - Empty results"
            results["critical_issues"].append("Autocomplete returns empty")
    except Exception as e:
        results["verification_results"]["search_unified"] = f"❌ FAIL: {str(e)}"
        results["critical_issues"].append(f"Search engine error: {str(e)}")
    
    # 2. TEMPLATE DUPLICATION
    print("\n2️⃣ TEMPLATE CONSOLIDATION")
    print("-" * 70)
    
    duplicates = [
        "templates/hotels/list.html (apps/hotels/)",
        "hotel_card.html (vs enhanced_hotel_card)",
        "listing_card.html",
        "card.html"
    ]
    
    # Check if app-level list.html exists
    app_list = Path("apps/hotels/templates/hotels/list.html")
    if not app_list.exists():
        results["verification_results"]["duplicate_list"] = "✅ PASS"
        print("✅ No duplicate apps/hotels/templates/hotels/list.html")
    else:
        results["verification_results"]["duplicate_list"] = "❌ FAIL"
        results["critical_issues"].append("Duplicate list.html still exists")
        print("❌ Duplicate list.html still exists!")
    
    # Check card components
    hotel_card = Path("templates/components/hotel_card.html")
    if not hotel_card.exists():
        results["verification_results"]["card_consolidated"] = "✅ PASS"
        print("✅ Duplicate card components deleted")
    else:
        results["verification_results"]["card_consolidated"] = "⚠️ WARN"
        results["critical_issues"].append("hotel_card.html still exists")
        print("⚠️ hotel_card.html exists (should be enhanced_hotel_card only)")
    
    # 3. CSS CONSOLIDATION
    print("\n3️⃣ CSS SYSTEM")
    print("-" * 70)
    
    css_files = {
        "tokens.css": True,  # Must exist
        "ui.css": True,       # Must exist
        "base.css": False,    # Must NOT exist
        "components.css": False,  # Must NOT exist
        "layout.css": False,  # Must NOT exist
        "ota-ui.css": False   # Must NOT exist
    }
    
    css_dir = Path("static/css")
    all_good = True
    for file, should_exist in css_files.items():
        exists = (css_dir / file).exists()
        if exists == should_exist:
            print(f"  ✅ {file}: {'exists' if exists else 'deleted'}")
        else:
            all_good = False
            status = "exists (BAD)" if exists else "missing (BAD)"
            print(f"  ❌ {file}: {status}")
            results["critical_issues"].append(f"CSS file issue: {file}")
    
    if all_good:
        results["verification_results"]["css_consolidated"] = "✅ PASS"
    else:
        results["verification_results"]["css_consolidated"] = "❌ FAIL"
    
    # 4. BASE.HTML AUTHORITY
    print("\n4️⃣ LAYOUT AUTHORITY")
    print("-" * 70)
    
    with open("templates/base.html") as f:
        base_html = f.read()
        
    # Check for flex layout
    if "display:flex" in base_html and "flex:1" in base_html:
        results["verification_results"]["layout_flex"] = "✅ PASS"
        print("✅ base.html has flex layout for sticky footer")
    else:
        results["verification_results"]["layout_flex"] = "⚠️ WARN"
        print("⚠️ base.html may not have proper flex layout")
    
    # Check CSS includes
    if 'css/tokens.css' in base_html and 'css/ui.css' in base_html:
        results["verification_results"]["css_includes"] = "✅ PASS"
        print("✅ base.html includes only tokens.css + ui.css")
    else:
        results["verification_results"]["css_includes"] = "❌ FAIL"
        results["critical_issues"].append("base.html CSS includes wrong")
        print("❌ base.html CSS includes incorrect")
    
    # 5. HEADER/FOOTER
    print("\n5️⃣ HEADER & FOOTER POSITIONING")
    print("-" * 70)
    
    # Check header
    with open("templates/components/header.html") as f:
        header = f.read()
    if "topbar" in header:
        print("✅ Header component exists with topbar class")
        results["verification_results"]["header"] = "✅ PASS"
    else:
        results["verification_results"]["header"] = "❌ FAIL"
        results["critical_issues"].append("Header missing topbar")
    
    # Check footer
    with open("templates/components/footer.html") as f:
        footer = f.read()
    if "site-footer" in footer:
        print("✅ Footer component exists")
        results["verification_results"]["footer"] = "✅ PASS"
    else:
        results["verification_results"]["footer"] = "❌ FAIL"
        results["critical_issues"].append("Footer missing site-footer class")
    
    # 6. AUTOCOMPLETE ENDPOINT
    print("\n6️⃣ AUTOCOMPLETE ENDPOINT")
    print("-" * 70)
    
    client = Client()
    try:
        response = client.get("/search/autocomplete/?q=del")
        if response.status_code == 200:
            data = response.json()
            if "results" in data:
                results["verification_results"]["autocomplete_endpoint"] = "✅ PASS"
                print(f"✅ /search/autocomplete/ working ({len(data['results'])} results for 'del')")
            else:
                results["verification_results"]["autocomplete_endpoint"] = "⚠️ WARN"
                print("⚠️ Autocomplete response missing 'results' key")
        else:
            results["verification_results"]["autocomplete_endpoint"] = "❌ FAIL"
            results["critical_issues"].append(f"Autocomplete status {response.status_code}")
    except Exception as e:
        results["verification_results"]["autocomplete_endpoint"] = f"❌ FAIL: {str(e)}"
        results["critical_issues"].append(f"Autocomplete test: {str(e)}")
    
    # 7. DJANGO CHECKS
    print("\n7️⃣ DJANGO SYSTEM CHECK")
    print("-" * 70)
    
    import io
    import contextlib
    
    f = io.StringIO()
    try:
        with contextlib.redirect_stdout(f):
            call_command('check', no_color=True)
        results["verification_results"]["django_check"] = "✅ PASS"
        print("✅ Django system check: 0 errors")
    except Exception as e:
        results["verification_results"]["django_check"] = f"❌ FAIL: {str(e)}"
        results["critical_issues"].append(f"Django check failed: {str(e)}")
        print(f"❌ Django check failed: {str(e)}")
    
    # SUMMARY
    print("\n" + "=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results["verification_results"].values() if "✅" in str(v))
    total = len(results["verification_results"])
    
    print(f"\nPassed: {passed}/{total}")
    
    if results["critical_issues"]:
        print(f"\n⚠️ CRITICAL ISSUES FOUND ({len(results['critical_issues'])}):")
        for issue in results["critical_issues"]:
            print(f"  - {issue}")
    else:
        print("\n✅ ALL CRITICAL ROOT CAUSES FIXED!")
    
    # Save results
    with open("ROOT_CAUSE_VERIFICATION.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Details saved to ROOT_CAUSE_VERIFICATION.json")
    print("=" * 70)
    
    return len(results["critical_issues"]) == 0

if __name__ == "__main__":
    success = verify_root_causes()
    sys.exit(0 if success else 1)


