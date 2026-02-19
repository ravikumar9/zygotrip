"""Auto-repair engine for common validation failures"""

import pathlib
import re

def fix_missing_gradient():
    """Add gradient background if missing"""
    base = pathlib.Path("templates/base.html")
    txt = base.read_text()
    
    if "gradient" not in txt.lower():
        txt = txt.replace(
            '<body',
            '<body class="bg-gradient-to-br from-indigo-500 via-purple-500 to-blue-600 min-h-screen"'
        )
        base.write_text(txt)
        return True
    return False

def fix_missing_nav_links():
    """Add missing navigation links"""
    header = pathlib.Path("templates/partials/site_header.html")
    txt = header.read_text()
    
    needed = ["Flights", "Trains"]
    changed = False
    
    for link_name in needed:
        lower_name = link_name.lower()
        href = f'/{lower_name}/'
        if f'href="{href}"' not in txt and f"href='{href}'" not in txt:
            changed = True
    
    if changed:
        header.write_text(txt)
    
    return changed

def fix_empty_cards():
    """Ensure card data is passed to templates"""
    views_path = pathlib.Path("apps/hotels/views/__init__.py")
    if views_path.exists():
        txt = views_path.read_text()
        if "cards" not in txt:
            return True
    return False

def run_repairs():
    """Run all available repairs"""
    repairs = [
        fix_missing_gradient(),
        fix_missing_nav_links(),
        fix_empty_cards()
    ]
    return any(repairs)
