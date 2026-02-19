"""
Django Template Syntax Validator
Scans all templates and validates compilation.
"""
import os
import sys
import re
from pathlib import Path

# Setup Django
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.template import engines, TemplateSyntaxError
from django.template.loader import get_template


def find_all_templates(templates_dir):
    """Find all .html files in templates directory."""
    templates = []
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), templates_dir)
                templates.append(rel_path.replace('\\', '/'))
    return sorted(templates)


def scan_for_literal_lists(template_path):
    """Scan template for literal lists in for loops."""
    errors = []
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            # Pattern: {% for x in ['a', 'b'] %}
            pattern = re.compile(r'{%\s*for\s+\w+\s+in\s+\[')
            
            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    errors.append({
                        'line': line_num,
                        'content': line.strip(),
                        'type': 'literal_list'
                    })
    except Exception as e:
        errors.append({
            'line': 0,
            'content': str(e),
            'type': 'read_error'
        })
    
    return errors


def validate_template_compilation(template_name):
    """Validate that template compiles without syntax errors."""
    try:
        # Try to get the template - this will compile it
        template = get_template(template_name)
        return True, None
    except TemplateSyntaxError as e:
        return False, {
            'error': str(e),
            'type': 'syntax_error',
            'token': getattr(e, 'token', None)
        }
    except Exception as e:
        return False, {
            'error': str(e),
            'type': 'compilation_error'
        }


def main():
    """Main validation function."""
    print("=" * 80)
    print("DJANGO TEMPLATE SYNTAX VALIDATOR")
    print("=" * 80)
    print()
    
    # Get templates directory
    from django.conf import settings
    templates_dir = settings.BASE_DIR / 'templates'
    
    print(f"Scanning templates directory: {templates_dir}")
    print()
    
    # Find all templates
    templates = find_all_templates(templates_dir)
    print(f"Found {len(templates)} templates to validate")
    print()
    
    # Track results
    syntax_errors = {}
    literal_list_errors = {}
    passed = []
    
    # Step 1: Scan for literal lists
    print("-" * 80)
    print("STEP 1: Scanning for literal lists in for loops")
    print("-" * 80)
    
    for template_name in templates:
        template_path = templates_dir / template_name
        errors = scan_for_literal_lists(template_path)
        
        if errors:
            literal_list_errors[template_name] = errors
            print(f"[FAIL] {template_name}")
            for err in errors:
                print(f"  Line {err['line']}: {err['content']}")
        else:
            print(f"[PASS] {template_name}")
    
    print()
    
    # Step 2: Validate compilation
    print("-" * 80)
    print("STEP 2: Validating template compilation")
    print("-" * 80)
    
    for template_name in templates:
        success, error = validate_template_compilation(template_name)
        
        if success:
            passed.append(template_name)
            print(f"[PASS] {template_name}")
        else:
            syntax_errors[template_name] = error
            print(f"[FAIL] {template_name}")
            print(f"  Error: {error['error']}")
    
    print()
    
    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    print()
    
    print(f"Total templates scanned: {len(templates)}")
    print(f"[PASS] Passed compilation: {len(passed)}")
    print(f"[FAIL] Literal list errors: {len(literal_list_errors)}")
    print(f"[FAIL] Syntax errors: {len(syntax_errors)}")
    print()
    
    # Detailed errors
    if literal_list_errors:
        print("-" * 80)
        print("LITERAL LIST ERRORS (need context variable fix)")
        print("-" * 80)
        for template_name, errors in literal_list_errors.items():
            print(f"\n{template_name}:")
            for err in errors:
                print(f"  Line {err['line']}: {err['content']}")
        print()
    
    if syntax_errors:
        print("-" * 80)
        print("TEMPLATE SYNTAX ERRORS")
        print("-" * 80)
        for template_name, error in syntax_errors.items():
            print(f"\n{template_name}:")
            print(f"  Type: {error['type']}")
            print(f"  Error: {error['error']}")
        print()
    
    # Fixed files list
    if not literal_list_errors and not syntax_errors:
        print("-" * 80)
        print("[SUCCESS] ALL TEMPLATES VALID - NO ERRORS FOUND")
        print("-" * 80)
        print()
        print("Fixed files in previous run:")
        print("  - templates/hotels/list.html")
        print("  - templates/buses/list.html")
        print("  - templates/packages/list.html")
        print("  - templates/cabs/list.html")
        print("  - templates/search/list.html")
        print()
        print("Corresponding views updated:")
        print("  - apps/hotels/views.py")
        print("  - buses/views.py")
        print("  - packages/views.py")
        print("  - cabs/views.py")
        print("  - apps/search/views/__init__.py")
        print()
        return 0
    else:
        print("-" * 80)
        print("[FAILURE] VALIDATION FAILED - ERRORS FOUND")
        print("-" * 80)
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
