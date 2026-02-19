#!/usr/bin/env python3
"""Template Audit and Repair Script"""
from pathlib import Path
import re
from collections import defaultdict

ROOT = Path('templates')
FIXES = defaultdict(list)
ERRORS = defaultdict(list)

def fix_html_after_endblock(path, text):
    """Remove HTML/content after final {% endblock %}"""
    match = re.search(r'({%\s*endblock\s*%})\s*(.+)', text, re.DOTALL)
    if match and match.group(2).strip():
        # Keep everything up to and including the last endblock
        last_endblock = text.rfind('{% endblock %}')
        if last_endblock != -1:
            # Find actual position including closing %}
            end_pos = text.find('%}', last_endblock) + 2
            new_text = text[:end_pos] + '\n'
            FIXES[str(path.relative_to(ROOT))].append(
                f"Remove {len(text) - end_pos} chars of content after final endblock"
            )
            return new_text
    return text

def fix_unmatched_blocks(path, text):
    """Fix unmatched block tags"""
    opens = len(re.findall(r'{%\s*block\s+\w+', text))
    closes = len(re.findall(r'{%\s*endblock\s*%}', text))
    
    if opens > closes:
        # Add missing endblocks
        new_text = text.rstrip() + '\n{% endblock %}\n' * (opens - closes)
        FIXES[str(path.relative_to(ROOT))].append(
            f"Add {opens - closes} missing endblock(s)"
        )
        return new_text
    elif closes > opens:
        # Remove extra endblocks
        lines = text.split('\n')
        result = []
        endblock_count = 0
        block_count = 0
        for line in lines:
            if '{% block ' in line:
                block_count += 1
            if '{% endblock %}' in line:
                if endblock_count < block_count:
                    result.append(line)
                    endblock_count += 1
            else:
                result.append(line)
        new_text = '\n'.join(result)
        FIXES[str(path.relative_to(ROOT))].append(
            f"Remove {closes - opens} extra endblock(s)"
        )
        return new_text
    return text

def remove_html_tags_outside_base(path, text):
    """Remove <html>, <body> tags from non-base files"""
    if 'base.html' in str(path):
        return text
    
    original = text
    text = re.sub(r'</body>\s*</html>\s*$', '', text)
    text = re.sub(r'^<html[^>]*>\s*', '', text)
    text = re.sub(r'^<body[^>]*>\s*', '', text)
    text = re.sub(r'^\s*<!DOCTYPE[^>]*>\s*', '', text)
    
    if text != original:
        FIXES[str(path.relative_to(ROOT))].append(
            "Remove non-base HTML structural tags"
        )
    return text

def remove_navbar_footer_duplicates(path, text):
    """Remove navbar/footer from non-base files"""
    if 'base.html' in str(path):
        return text
    
    original = text
    # Remove navbar/footer includes
    text = re.sub(
        r'\s*{%\s*include\s*["\']partials/site_(?:header|footer|navbar)\.html["\'].*?%}\s*',
        '', text, flags=re.DOTALL
    )
    
    # Remove standalone header/footer HTML
    text = re.sub(r'<header[^>]*>.*?</header>\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'<nav[^>]*>.*?</nav>\s*', '', text, flags=re.DOTALL)
    text = re.sub(r'^<footer[^>]*>.*?</footer>\s*', '', text, flags=re.DOTALL)
    
    if text != original:
        FIXES[str(path.relative_to(ROOT))].append(
            "Remove duplicate navbar/footer markup"
        )
    return text

def fix_extends_format(path, text):
    """Normalize extends to use double quotes and base.html path"""
    if not text.strip().startswith('{%'):
        return text
    
    original = text
    # Normalize extends to base.html
    text = re.sub(
        r'{%\s*extends\s+["\']layouts/base_marketplace\.html["\']',
        '{% extends "layouts/marketplace_layout.html" %}',
        text
    )
    # Standardize quotes to double
    text = re.sub(
        r"{%\s*extends\s+'([^']+)'",
        r'{% extends "\1" %}',
        text
    )
    
    if text != original:
        FIXES[str(path.relative_to(ROOT))].append(
            "Normalize extends format"
        )
    return text

def fix_partials(path, text):
    """Ensure partials have no extends/blocks"""
    if '/partials/' not in str(path):
        return text
    
    original = text
    if re.search(r'{%\s*extends', text):
        text = re.sub(r'{%\s*extends[^%]*%}\s*\n', '', text)
        FIXES[str(path.relative_to(ROOT))].append(
            "Remove extends from partial"
        )
    
    if re.search(r'{%\s*block\s+\w+', text) or re.search(r'{%\s*endblock', text):
        text = re.sub(r'{%\s*block\s+\w+\s*%}', '', text)
        text = re.sub(r'{%\s*endblock\s*%}', '', text)
        FIXES[str(path.relative_to(ROOT))].append(
            "Remove block tags from partial"
        )
    
    return text

def process_file(path):
    """Apply all fixes to a file"""
    try:
        text = path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        ERRORS[str(path.relative_to(ROOT))].append(str(e))
        return
    
    # Apply fixes in order
    text = fix_html_after_endblock(path, text)
    text = fix_unmatched_blocks(path, text)
    text = remove_html_tags_outside_base(path, text)
    text = remove_navbar_footer_duplicates(path, text)
    text = fix_extends_format(path, text)
    text = fix_partials(path, text)
    
    # Write back
    try:
        path.write_text(text, encoding='utf-8')
    except Exception as e:
        ERRORS[str(path.relative_to(ROOT))].append(f"Write error: {e}")

# Process all templates
for path in sorted(ROOT.rglob('*.html')):
    process_file(path)

# Report
print("\n" + "=" * 80)
print("TEMPLATE AUDIT AND REPAIR REPORT")
print("=" * 80)

if FIXES:
    print(f"\nFIXED: {sum(len(v) for v in FIXES.values())} issues in {len(FIXES)} files\n")
    for fname in sorted(FIXES.keys()):
        print(f"  {fname}")
        for fix in FIXES[fname]:
            print(f"    ✓ {fix}")

if ERRORS:
    print(f"\nERRORS: {len(ERRORS)} files\n")
    for fname in sorted(ERRORS.keys()):
        print(f"  {fname}")
        for err in ERRORS[fname]:
            print(f"    ✗ {err}")

print("\n" + "=" * 80)
