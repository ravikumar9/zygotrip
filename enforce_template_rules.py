#!/usr/bin/env python3
"""
Django Template Architecture Rule Enforcement
Auto-fixes violations where safe, reports manual fix requirements.
"""

from pathlib import Path
import re
from collections import defaultdict

root = Path('templates')

report = {
    'fixed': [],
    'manual': [],
    'stats': {
        'total_scanned': 0,
        'violations_found': 0,
        'auto_fixed': 0,
        'manual_required': 0,
    }
}

def is_page_template(rel_path):
    """Determine if file is a page template."""
    if 'partials' in rel_path or 'layouts' in rel_path:
        return False
    if rel_path == 'base.html':
        return False
    # Page templates typically have list/detail/booking/dashboard/login/register
    return any(x in rel_path for x in [
        '/list.html', '/detail.html', '/booking', '/review', 
        '/dashboard', '/login', '/register', '/profile', '/home',
        '/success', '/payment', '/invoice', '/not_found'
    ])

def is_layout_template(rel_path):
    """Determine if file is a layout template."""
    return 'layouts' in rel_path or (rel_path.startswith('base_') and rel_path != 'base.html')

def is_partial_template(rel_path):
    """Determine if file is a partial template."""
    return 'partials' in rel_path

def scan_and_fix_file(fpath):
    """Scan single file for violations and auto-fix where possible."""
    content = fpath.read_text(encoding='utf-8', errors='ignore')
    original = content
    rel_path = str(fpath.relative_to(root))
    
    report['stats']['total_scanned'] += 1
    
    issues_fixed = []
    manual_issues = []
    
    # ========================================================================
    # RULE 1: Page templates must start with extends
    # ========================================================================
    if is_page_template(rel_path):
        if not content.strip().startswith('{% extends'):
            # Check if extends exists anywhere
            if '{% extends' in content:
                manual_issues.append({
                    'rule': 'RULE 1: Page extends tag position',
                    'issue': 'Extends tag exists but not at start of file',
                    'reason': 'Manual repositioning required to avoid breaking logic'
                })
            else:
                # Auto-fix: insert extends at top
                content = '{% extends "base.html" %}\n\n' + content
                issues_fixed.append('Added missing extends tag at file start')
    
    # ========================================================================
    # RULE 2: Layout templates must extend base.html
    # ========================================================================
    if is_layout_template(rel_path):
        if '{% extends' not in content:
            content = '{% extends "base.html" %}\n\n' + content
            issues_fixed.append('Added missing extends to layout')
        elif not re.search(r'{%\s*extends\s+["\']base\.html["\']', content):
            # Layout extends something other than base.html
            content = re.sub(
                r'{%\s*extends\s+["\'][^"\']+["\']',
                '{% extends "base.html"',
                content,
                count=1
            )
            issues_fixed.append('Fixed layout to extend base.html')
    
    # ========================================================================
    # RULE 3: Partials must not contain extends or block
    # ========================================================================
    if is_partial_template(rel_path):
        if re.search(r'{%\s*extends', content):
            content = re.sub(r'{%\s*extends\s+["\'][^"\']*["\']\s*%}\n?', '', content)
            issues_fixed.append('Removed extends from partial')
        
        if re.search(r'{%\s*block\s+\w+', content):
            # Remove block tags entirely from partials
            content = re.sub(r'{%\s*block\s+\w+[^%]*%}\n?', '', content)
            content = re.sub(r'{%\s*endblock[^%]*%}\n?', '', content)
            issues_fixed.append('Removed block tags from partial')
    
    # ========================================================================
    # RULE 4: Only base.html may contain body tag
    # ========================================================================
    if rel_path != 'base.html':
        if re.search(r'<body[\s>]', content, re.IGNORECASE):
            content = re.sub(r'<body[^>]*>\n?', '', content, flags=re.IGNORECASE)
            content = re.sub(r'</body>\n?', '', content, flags=re.IGNORECASE)
            issues_fixed.append('Removed body tags from non-base template')
        
        # Also remove other HTML structure tags
        if re.search(r'<!DOCTYPE|<html[\s>]', content, re.IGNORECASE):
            content = re.sub(r'<!DOCTYPE[^>]*>\n?', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<html[^>]*>\n?', '', content, flags=re.IGNORECASE)
            content = re.sub(r'</html>\n?', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<head[^>]*>.*?</head>\n?', '', content, flags=re.DOTALL | re.IGNORECASE)
            issues_fixed.append('Removed HTML structure tags')
    
    # ========================================================================
    # RULE 5: No HTML after endblock
    # ========================================================================
    # Find FINAL endblock
    endblock_matches = list(re.finditer(r'{%\s*endblock\s*%}', content))
    if endblock_matches:
        last_endblock = endblock_matches[-1]
        after_endblock = content[last_endblock.end():].strip()
        
        # Allow closing tags that belong to base.html structure
        if rel_path == 'base.html':
            # base.html is allowed to have </div></main></body></html> after endblock
            pass
        else:
            # Check if there's actual content (not just whitespace/common closing tags)
            if after_endblock and after_endblock not in ['</div>', '</main>', '</section>']:
                # Check for actual HTML/template content
                if re.search(r'<[a-z]|{%|{{', after_endblock, re.IGNORECASE):
                    # Remove everything after the final endblock
                    content = content[:last_endblock.end()] + '\n'
                    issues_fixed.append(f'Removed {len(after_endblock)} chars after final endblock')
    
    # ========================================================================
    # RULE 6: Header/footer includes only in base.html
    # ========================================================================
    if rel_path != 'base.html':
        if 'site_header.html' in content or 'site_footer.html' in content:
            # Check if it's in an include statement
            if re.search(r'{%\s*include\s+["\'](?:partials/)?site_(?:header|footer)\.html', content):
                manual_issues.append({
                    'rule': 'RULE 6: Header/footer includes',
                    'issue': 'Template includes site_header/footer but only base.html should',
                    'reason': 'Review needed to ensure no duplicate navigation'
                })
    
    # ========================================================================
    # RULE 7: Layout files must not have loops or variables
    # ========================================================================
    if is_layout_template(rel_path):
        has_loops = bool(re.search(r'{%\s*(?:for|if)\s+\w+', content))
        has_variables = bool(re.findall(r'{{\s*[a-z_]\w*\s*}}', content))
        
        if has_loops:
            manual_issues.append({
                'rule': 'RULE 7: Layout purity',
                'issue': 'Layout contains loops/conditionals (for/if)',
                'reason': 'Move data rendering logic to page templates'
            })
        
        if has_variables and not re.search(r'{{\s*block\.super\s*}}', content):
            # Ignore block.super, focus on actual variables
            vars_found = re.findall(r'{{\s*([a-z_]\w*)\s*}}', content)
            if vars_found and not all(v in ['user', 'request'] for v in vars_found):
                manual_issues.append({
                    'rule': 'RULE 7: Layout purity',
                    'issue': f'Layout contains template variables: {", ".join(set(vars_found[:3]))}',
                    'reason': 'Move variable rendering to page templates'
                })
    
    # ========================================================================
    # Write back if changed
    # ========================================================================
    if content != original:
        fpath.write_text(content, encoding='utf-8')
        
        if issues_fixed:
            report['fixed'].append({
                'file': rel_path,
                'issues': issues_fixed
            })
            report['stats']['auto_fixed'] += len(issues_fixed)
            report['stats']['violations_found'] += len(issues_fixed)
    
    if manual_issues:
        for issue in manual_issues:
            report['manual'].append({
                'file': rel_path,
                **issue
            })
            report['stats']['manual_required'] += 1
            report['stats']['violations_found'] += 1

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print("\n" + "=" * 80)
print("DJANGO TEMPLATE ARCHITECTURE ENFORCEMENT")
print("=" * 80)

# Scan all HTML files
for fpath in sorted(root.rglob('*.html')):
    scan_and_fix_file(fpath)

# ============================================================================
# REPORT OUTPUT
# ============================================================================

print("\n" + "-" * 80)
print("SECTION: FIXED FILES")
print("-" * 80)

if report['fixed']:
    for item in report['fixed']:
        print(f"\n{item['file']}")
        for issue in item['issues']:
            print(f"  • {issue}")
else:
    print("\nNone - No auto-fixable violations detected")

print("\n" + "-" * 80)
print("SECTION: MANUAL FIX REQUIRED")
print("-" * 80)

if report['manual']:
    for item in report['manual']:
        print(f"\n{item['file']}")
        print(f"  Rule: {item['rule']}")
        print(f"  Issue: {item['issue']}")
        print(f"  Reason: {item['reason']}")
else:
    print("\nNone - All violations were auto-fixed")

print("\n" + "-" * 80)
print("SECTION: FINAL STATUS")
print("-" * 80)

print(f"\nTemplates Scanned: {report['stats']['total_scanned']}")
print(f"Violations Found: {report['stats']['violations_found']}")
print(f"Auto-Fixed: {report['stats']['auto_fixed']}")
print(f"Manual Required: {report['stats']['manual_required']}")

if report['stats']['manual_required'] == 0:
    status = "PASS"
    message = "All rules enforced - system compliant"
else:
    status = "FAIL"
    message = f"{report['stats']['manual_required']} violations require manual review"

print(f"\nFinal Status: {status}")
print(f"Message: {message}")

print("\n" + "=" * 80 + "\n")
