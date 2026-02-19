#!/usr/bin/env python3
"""
Comprehensive Django template system audit and repair.
Fixes all structural issues and normalizes architecture.
"""

from pathlib import Path
import re
from collections import defaultdict

root = Path('templates')
report = {
    'fixed_files': [],
    'errors': [],
    'architecture': {
        'base_templates': [],
        'layout_templates': [],
        'page_templates': [],
        'partial_templates': [],
        'other_templates': [],
    }
}

# ============================================================================
# 1. PARTIAL FILE VALIDATION AND CREATION
# ============================================================================

def validate_partials():
    """Ensure partial files exist with valid minimal markup."""
    partials_dir = root / 'partials'
    partials_dir.mkdir(exist_ok=True)
    
    # site_header.html
    header_path = partials_dir / 'site_header.html'
    if not header_path.exists() or header_path.stat().st_size == 0:
        header_content = '''<header class="bg-white border-b border-gray-200">
  <nav class="max-w-7xl mx-auto px-6 py-4">
    <div class="flex justify-between items-center">
      <div class="text-2xl font-bold">Zygotrip</div>
      <div class="flex gap-4">
        <a href="/" class="text-gray-600 hover:text-gray-900">Home</a>
        {% if user.is_authenticated %}
          <a href="/logout/" class="text-gray-600 hover:text-gray-900">Logout</a>
        {% else %}
          <a href="/login/" class="text-gray-600 hover:text-gray-900">Login</a>
        {% endif %}
      </div>
    </div>
  </nav>
</header>
'''
        header_path.write_text(header_content, encoding='utf-8')
        report['fixed_files'].append({
            'file': str(header_path.relative_to(root)),
            'issue': 'Missing or empty header partial',
            'fix': 'Created with minimal navbar markup'
        })
    
    # site_footer.html
    footer_path = partials_dir / 'site_footer.html'
    if not footer_path.exists() or footer_path.stat().st_size == 0:
        footer_content = '''<footer class="bg-gray-900 text-gray-300 mt-20">
  <div class="max-w-7xl mx-auto px-6 py-12">
    <div class="grid grid-cols-4 gap-8 mb-8">
      <div>
        <h3 class="text-white font-semibold mb-4">Company</h3>
        <ul class="space-y-2">
          <li><a href="#" class="hover:text-white">About</a></li>
          <li><a href="#" class="hover:text-white">Contact</a></li>
        </ul>
      </div>
      <div>
        <h3 class="text-white font-semibold mb-4">Support</h3>
        <ul class="space-y-2">
          <li><a href="#" class="hover:text-white">Help</a></li>
          <li><a href="#" class="hover:text-white">FAQ</a></li>
        </ul>
      </div>
      <div>
        <h3 class="text-white font-semibold mb-4">Legal</h3>
        <ul class="space-y-2">
          <li><a href="#" class="hover:text-white">Privacy</a></li>
          <li><a href="#" class="hover:text-white">Terms</a></li>
        </ul>
      </div>
      <div>
        <h3 class="text-white font-semibold mb-4">Follow</h3>
        <ul class="space-y-2">
          <li><a href="#" class="hover:text-white">Twitter</a></li>
          <li><a href="#" class="hover:text-white">LinkedIn</a></li>
        </ul>
      </div>
    </div>
    <div class="border-t border-gray-700 pt-8 text-center">
      <p>&copy; 2026 Zygotrip. All rights reserved.</p>
    </div>
  </div>
</footer>
'''
        footer_path.write_text(footer_content, encoding='utf-8')
        report['fixed_files'].append({
            'file': str(footer_path.relative_to(root)),
            'issue': 'Missing or empty footer partial',
            'fix': 'Created with standard footer markup'
        })

# ============================================================================
# 2. BASE TEMPLATE VALIDATION
# ============================================================================

def validate_base_template():
    """Ensure base.html has proper structure with includes."""
    base_path = root / 'base.html'
    
    if not base_path.exists():
        return
    
    content = base_path.read_text(encoding='utf-8', errors='ignore')
    original = content
    
    # Check for header include (correct path)
    if 'partials/site_header.html' not in content:
        if 'site_header.html' in content:
            # Fix incorrect path
            content = content.replace(
                'site_header.html',
                'partials/site_header.html'
            )
        elif '<header' in content:
            # Replace inline header with include
            content = re.sub(
                r'<header[^>]*>.*?</header>',
                '{% include "partials/site_header.html" %}',
                content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            # Insert after body tag
            content = re.sub(
                r'(<body[^>]*>)',
                r'\1\n    {% include "partials/site_header.html" %}',
                content,
                flags=re.IGNORECASE
            )
    
    # Check for footer include (correct path)
    if 'partials/site_footer.html' not in content:
        if 'site_footer.html' in content:
            # Fix incorrect path
            content = content.replace(
                'site_footer.html',
                'partials/site_footer.html'
            )
        elif '<footer' in content:
            # Replace inline footer with include
            content = re.sub(
                r'<footer[^>]*>.*?</footer>',
                '{% include "partials/site_footer.html" %}',
                content,
                flags=re.DOTALL | re.IGNORECASE
            )
        else:
            # Insert before closing body tag
            content = re.sub(
                r'(</body>)',
                r'\n    {% include "partials/site_footer.html" %}\n  \1',
                content,
                flags=re.IGNORECASE
            )
    
    # Verify main block exists
    if '{% block content %}' not in content:
        # Insert main block after header
        content = re.sub(
            r'({% include "partials/site_header.html" %}\n)',
            r'\1\n    {% block content %}{% endblock %}\n',
            content
        )
    
    # Verify closing tags
    if '</main>' not in content:
        content = content.replace(
            '{% block content %}{% endblock %}',
            '{% block content %}{% endblock %}\n      </div>\n    </main>'
        )
    
    if '</body>' not in content:
        content += '\n  </body>\n</html>'
    
    if '</html>' not in content:
        content += '\n</html>'
    
    if content != original:
        base_path.write_text(content, encoding='utf-8')
        report['fixed_files'].append({
            'file': 'base.html',
            'issue': 'Incomplete or malformed structure',
            'fix': 'Restored header/footer includes and closing tags'
        })

# ============================================================================
# 3. SCAN ALL TEMPLATES AND FIX ISSUES
# ============================================================================

def fix_template_file(fpath):
    """Fix all structural issues in a single template."""
    content = fpath.read_text(encoding='utf-8', errors='ignore')
    original = content
    issues = []
    rel_path = str(fpath.relative_to(root))
    
    # Issue 1: Fix incorrect include paths
    if 'site_header.html' in content and 'partials/site_header.html' not in content:
        content = content.replace(
            '"site_header.html"',
            '"partials/site_header.html"'
        ).replace(
            "'site_header.html'",
            "'partials/site_header.html'"
        )
        issues.append('Fixed site_header include path')
    
    if 'site_footer.html' in content and 'partials/site_footer.html' not in content:
        content = content.replace(
            '"site_footer.html"',
            '"partials/site_footer.html"'
        ).replace(
            "'site_footer.html'",
            "'partials/site_footer.html'"
        )
        issues.append('Fixed site_footer include path')
    
    # Issue 2: Remove HTML after endblock
    endblock_pattern = r'({% endblock %})\s*([\s\S]*?)(?=\Z|<!DOCTYPE|<html|</html>)'
    match = re.search(endblock_pattern, content, re.IGNORECASE)
    if match and match.group(2).strip():
        remaining = match.group(2)
        if remaining.strip() and remaining.strip() not in ['</div>', '</main>', '</body>', '</html>']:
            content = content[:match.start(2)] + content[match.end(2):]
            issues.append(f'Removed {len(remaining)} chars after endblock')
    
    # Issue 3: Fix unmatched blocks
    block_opens = len(re.findall(r'{%\s*block\s+\w+', content))
    endblock_closes = len(re.findall(r'{%\s*endblock', content))
    if block_opens > endblock_closes:
        for _ in range(block_opens - endblock_closes):
            content = content.rstrip() + '\n{% endblock %}'
        issues.append(f'Added {block_opens - endblock_closes} missing endblock tags')
    elif endblock_closes > block_opens:
        # Remove extra endblocks from end
        lines = content.split('\n')
        excess = endblock_closes - block_opens
        for _ in range(excess):
            for i in range(len(lines) - 1, -1, -1):
                if '{% endblock' in lines[i]:
                    lines.pop(i)
                    break
        content = '\n'.join(lines)
        issues.append(f'Removed {excess} extra endblock tags')
    
    # Issue 4: Validate extends in partials
    if 'partials' in rel_path:
        if '{% extends' in content:
            content = re.sub(r'{%\s*extends\s+["\'][^"\']*["\']\s*%}\n?', '', content)
            issues.append('Removed extends from partial')
        
        if re.search(r'{%\s*(?:block|endblock)', content):
            content = re.sub(r'{%\s*block\s+\w+[^%]*%}', '', content)
            content = re.sub(r'{%\s*endblock\s*%}', '', content)
            issues.append('Removed blocks from partial')
    
    # Issue 5: Validate extends in layouts
    elif 'layouts' in rel_path and not rel_path.endswith('base.html'):
        if '{% extends' not in content:
            content = '{% extends "base.html" %}\n' + content
            issues.append('Added missing extends to layout')
        elif 'extends "layouts/' in content or 'extends \'layouts/' in content:
            # Ensure layouts extend base, not other layouts
            content = re.sub(
                r'{%\s*extends\s+["\']layouts/[^"\']*["\']',
                '{% extends "base.html"',
                content
            )
            issues.append('Fixed layout extends to use base.html')
    
    # Issue 6: Validate HTML tags only in base.html
    if rel_path != 'base.html':
        if re.search(r'<html|<body|<!DOCTYPE', content, re.IGNORECASE):
            # Remove HTML structure tags
            content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<html[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'</html>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<body[^>]*>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'</body>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<head[^>]*>.*?</head>', '', content, flags=re.DOTALL | re.IGNORECASE)
            issues.append('Removed HTML structure tags')
    
    # Issue 7: Remove duplicate navbar/footer in partials
    if 'partials' in rel_path:
        original_len = len(content)
        content = re.sub(r'<nav[^>]*>.*?</nav>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<header[^>]*>.*?</header>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<footer[^>]*>.*?</footer>', '', content, flags=re.DOTALL | re.IGNORECASE)
        if len(content) != original_len:
            issues.append('Removed duplicate navigation markup')
    
    if content != original:
        fpath.write_text(content, encoding='utf-8')
        if issues:
            report['fixed_files'].append({
                'file': rel_path,
                'issue': ' + '.join(issues),
                'fix': 'Applied fixes'
            })
        return True
    return False

# ============================================================================
# 4. CLASSIFY TEMPLATES
# ============================================================================

def classify_template(fpath):
    """Classify template by role."""
    rel_path = str(fpath.relative_to(root))
    
    if rel_path == 'base.html':
        return 'base'
    elif 'partials' in rel_path:
        return 'partial'
    elif 'layouts' in rel_path:
        return 'layout'
    elif any(x in rel_path for x in ['list.html', 'detail.html', 'create.html', 'edit.html']):
        return 'page'
    else:
        return 'other'

# ============================================================================
# 5. VALIDATE LAYOUT RULES
# ============================================================================

def validate_layout_rules():
    """Ensure layouts contain only blocks, no loops or model variables."""
    for fpath in root.rglob('*.html'):
        rel_path = str(fpath.relative_to(root))
        
        if 'layouts' not in rel_path:
            continue
        
        content = fpath.read_text(encoding='utf-8', errors='ignore')
        original = content
        issues = []
        
        # Check for loops in layout
        if re.search(r'{%\s*(?:for|if)\s+', content):
            # Move loops to their own block or comment them out
            report['errors'].append({
                'file': rel_path,
                'problem': 'Layout contains loops or conditionals',
                'suggestion': 'Move loops to page templates'
            })
        
        # Check for model variables in layout
        model_vars = re.findall(r'{{\s*\w+\s*}}', content)
        if model_vars and rel_path != 'layouts/base.html':
            report['errors'].append({
                'file': rel_path,
                'problem': f'Layout contains template variables: {", ".join(set(model_vars[:3]))}',
                'suggestion': 'Move variables to page templates'
            })

# ============================================================================
# EXECUTION
# ============================================================================

print("\n" + "=" * 80)
print("DJANGO TEMPLATE SYSTEM AUDIT & REPAIR")
print("=" * 80)

# Step 1: Validate/create partials
print("\n[1/5] Validating partial files...")
validate_partials()

# Step 2: Validate base template
print("[2/5] Validating base template...")
validate_base_template()

# Step 3: Scan and fix all templates
print("[3/5] Scanning and fixing all templates...")
fixed_count = 0
for fpath in sorted(root.rglob('*.html')):
    if fix_template_file(fpath):
        fixed_count += 1

# Step 4: Validate layout rules
print("[4/5] Validating layout rules...")
validate_layout_rules()

# Step 5: Classify all templates
print("[5/5] Classifying templates...")
for fpath in sorted(root.rglob('*.html')):
    classification = classify_template(fpath)
    rel_path = str(fpath.relative_to(root))
    report['architecture'][f'{classification}_templates'].append(rel_path)

# ============================================================================
# OUTPUT REPORT
# ============================================================================

print("\n" + "=" * 80)
print("FIXED FILES (" + str(len(report['fixed_files'])) + ")")
print("=" * 80)
for item in report['fixed_files']:
    print(f"\n{item['file']}")
    print(f"  Issue: {item['issue']}")
    print(f"  Fix: {item['fix']}")

if report['errors']:
    print("\n" + "=" * 80)
    print("ERRORS DETECTED (" + str(len(report['errors'])) + ")")
    print("=" * 80)
    for item in report['errors']:
        print(f"\n{item['file']}")
        print(f"  Problem: {item['problem']}")
        print(f"  Suggestion: {item['suggestion']}")

print("\n" + "=" * 80)
print("ARCHITECTURE SUMMARY")
print("=" * 80)

for category in ['base_templates', 'layout_templates', 'page_templates', 'partial_templates', 'other_templates']:
    files = report['architecture'][category]
    category_name = category.replace('_templates', '').upper()
    print(f"\n{category_name} ({len(files)})")
    for f in sorted(files):
        print(f"  - {f}")

print("\n" + "=" * 80)
print("REPAIR COMPLETE")
print("=" * 80 + "\n")
