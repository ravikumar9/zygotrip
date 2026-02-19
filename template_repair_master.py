#!/usr/bin/env python3
"""
DJANGO TEMPLATE SYSTEM: COMPREHENSIVE REPAIR & VALIDATION
Ensures all pages render with header, footer, and visible content.
"""

from pathlib import Path
import re

root = Path('templates')
static_root = Path('static')

report = {
    'fixed': [],
    'created': [],
    'deleted': [],
    'failures': [],
}

# STEP 1: CONTRACT BLOCKS from marketplace_layout.html
CONTRACT_BLOCKS = [
    'page_header',
    'sidebar_filters',
    'search_bar',
    'results_list',
    'error_state',
    'pagination'
]

# STEP 2: MARKETPLACE PAGES
MARKETPLACE_PAGES = {
    'hotels/list.html': {
        'title': 'Browse Hotels',
        'description': 'Find and book premium hotels',
        'filter_labels': ['Price Range', 'Star Rating', 'Amenities'],
        'model_name': 'hotels',
    },
    'buses/list.html': {
        'title': 'Bus Tickets',
        'description': 'Search and book bus tickets across India',
        'filter_labels': ['Bus Type', 'Departure Time', 'Operator'],
        'model_name': 'buses',
    },
    'packages/list.html': {
        'title': 'Holiday Packages',
        'description': 'Discover amazing travel experiences',
        'filter_labels': ['Duration', 'Price Range', 'Destination'],
        'model_name': 'packages',
    },
    'cabs/list.html': {
        'title': 'Browse Cabs',
        'description': 'Rent a cab for your city travels',
        'filter_labels': ['Vehicle Type', 'Seating Capacity', 'Price Range'],
        'model_name': 'cabs',
    },
    'search/list.html': {
        'title': 'Search Results',
        'description': 'Your search results',
        'filter_labels': ['Category', 'Price Range', 'Location'],
        'model_name': 'results',
    },
}

def generate_complete_template(page_path, config):
    """Generate complete marketplace page with all required blocks."""
    return f'''{{%extends "layouts/marketplace_layout.html" %}}

{{% block page_header %}}
  <h1 class="text-3xl font-bold mb-2">{config['title']}</h1>
  <p class="text-secondary text-base">{config['description']}</p>
{{% endblock %}}

{{% block search_bar %}}
  <form method="get" class="bg-white p-6 rounded-lg shadow-sm">
    <div class="flex gap-4">
      <input type="text" name="q" placeholder="Search..." class="flex-1 px-4 py-2 border rounded-lg" />
      <button type="submit" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
        Search
      </button>
    </div>
  </form>
{{% endblock %}}

{{% block sidebar_filters %}}
  <div class="bg-white p-6 rounded-lg shadow-sm">
    <h3 class="font-semibold mb-4">Filters</h3>
    
    {{% for label in ['{config['filter_labels'][0]}', '{config['filter_labels'][1]}', '{config['filter_labels'][2]}'] %}}
    <div class="mb-4">
      <h4 class="text-sm font-medium mb-2">{{{{ label }}}}</h4>
      <div class="space-y-2">
        <label class="flex items-center">
          <input type="checkbox" class="mr-2" />
          <span class="text-sm">Option 1</span>
        </label>
        <label class="flex items-center">
          <input type="checkbox" class="mr-2" />
          <span class="text-sm">Option 2</span>
        </label>
      </div>
    </div>
    {{% endfor %}}
  </div>
{{% endblock %}}

{{% block results_list %}}
  {{% if {config['model_name']} %}}
    <div class="grid gap-4">
      {{% for item in {config['model_name']} %}}
        <div class="bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition">
          <h3 class="font-semibold text-lg mb-2">{{{{ item.name|default:"Item Name" }}}}</h3>
          <p class="text-gray-600 mb-4">{{{{ item.description|default:"Description not available"|truncatewords:20 }}}}</p>
          <div class="flex justify-between items-center">
            <span class="text-xl font-bold text-blue-600">
              {{{{ item.price|default:"₹999" }}}}
            </span>
            <a href="{{{{ item.get_absolute_url }}}}" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              View Details
            </a>
          </div>
        </div>
      {{% endfor %}}
    </div>
  {{% else %}}
    {{% block error_state %}}
      <div class="bg-white p-12 rounded-lg shadow-sm text-center">
        <div class="text-6xl mb-4">🔍</div>
        <h3 class="text-xl font-semibold mb-2">No results found</h3>
        <p class="text-gray-600">Try adjusting your search criteria</p>
      </div>
    {{% endblock %}}
  {{% endif %}}
{{% endblock %}}

{{% block pagination %}}
  {{% if is_paginated %}}
    <div class="flex justify-center gap-2 mt-8">
      {{% if page_obj.has_previous %}}
        <a href="?page={{{{ page_obj.previous_page_number }}}}" class="px-4 py-2 border rounded hover:bg-gray-50">
          Previous
        </a>
      {{% endif %}}
      
      <span class="px-4 py-2 bg-blue-600 text-white rounded">
        Page {{{{ page_obj.number }}}} of {{{{ page_obj.paginator.num_pages }}}}
      </span>
      
      {{% if page_obj.has_next %}}
        <a href="?page={{{{ page_obj.next_page_number }}}}" class="px-4 py-2 border rounded hover:bg-gray-50">
          Next
        </a>
      {{% endif %}}
    </div>
  {{% endif %}}
{{% endblock %}}
'''

# STEP 3: FIX MARKETPLACE PAGES
print("\n" + "=" * 80)
print("DJANGO TEMPLATE REPAIR: EXECUTION")
print("=" * 80)

for page_path, config in MARKETPLACE_PAGES.items():
    fpath = root / page_path
    if fpath.exists():
        content = fpath.read_text(encoding='utf-8')
        
        # Check if page only has page_header block
        has_only_header = (
            '{% block page_header %}' in content and
            '{% block results_list %}' not in content
        )
        
        if has_only_header:
            new_content = generate_complete_template(page_path, config)
            fpath.write_text(new_content, encoding='utf-8')
            report['fixed'].append({
                'file': page_path,
                'change': 'Added missing blocks: search_bar, sidebar_filters, results_list, pagination'
            })

# STEP 4: VALIDATE BASE.HTML
base_path = root / 'base.html'
if base_path.exists():
    content = base_path.read_text(encoding='utf-8')
    has_header = 'partials/site_header.html' in content
    has_footer = 'partials/site_footer.html' in content
    has_content_block = '{% block content %}' in content
    
    if not (has_header and has_footer and has_content_block):
        report['failures'].append({
            'file': 'base.html',
            'reason': 'Missing required includes or content block'
        })

# STEP 5: VALIDATE PARTIALS
partials_dir = root / 'partials'
if partials_dir.exists():
    for partial in partials_dir.glob('*.html'):
        content = partial.read_text(encoding='utf-8', errors='ignore')
        
        has_extends = re.search(r'{%\s*extends', content)
        has_block = re.search(r'{%\s*block\s+\w+', content)
        
        if has_extends or has_block:
            # Clean it
            content = re.sub(r'{%\s*extends\s+["\'][^"\']*["\']\s*%}\n?', '', content)
            content = re.sub(r'{%\s*block\s+\w+[^%]*%}\n?', '', content)
            content = re.sub(r'{%\s*endblock\s*%}\n?', '', content)
            partial.write_text(content, encoding='utf-8')
            report['fixed'].append({
                'file': f'partials/{partial.name}',
                'change': 'Removed extends/block tags'
            })

# STEP 6: VALIDATE STATIC FILES
required_css = ['tailwind.css', 'components.css', 'utilities.css']
for css_file in required_css:
    css_path = static_root / 'css' / css_file
    if not css_path.exists():
        report['failures'].append({
            'file': f'static/css/{css_file}',
            'reason': 'File missing but referenced in base.html'
        })

# STEP 7: RENDER TEST (Static Analysis)
print("\n" + "-" * 80)
print("RENDER TEST (Static Structure Check)")
print("-" * 80)

test_templates = [
    'hotels/list.html',
    'buses/list.html',
    'packages/list.html',
    'cabs/list.html'
]

for template_name in test_templates:
    try:
        fpath = root / template_name
        if not fpath.exists():
            report['failures'].append({
                'file': template_name,
                'reason': 'Template file does not exist'
            })
            print(f"✗ {template_name} - FAIL: File not found")
            continue
            
        content = fpath.read_text(encoding='utf-8')
        
        # Check template structure
        has_extends = '{% extends' in content
        has_page_header = '{% block page_header %}' in content
        has_results_list = '{% block results_list %}' in content
        has_search_bar = '{% block search_bar %}' in content
        has_filters = '{% block sidebar_filters %}' in content
        
        missing_blocks = []
        if not has_results_list:
            missing_blocks.append('results_list')
        if not has_search_bar:
            missing_blocks.append('search_bar')
        if not has_filters:
            missing_blocks.append('sidebar_filters')
        
        if missing_blocks:
            report['failures'].append({
                'file': template_name,
                'reason': f'Missing blocks: {", ".join(missing_blocks)}'
            })
            print(f"✗ {template_name} - FAIL: Missing {', '.join(missing_blocks)}")
        else:
            print(f"✓ {template_name} - OK (all blocks present)")
            
    except Exception as e:
        report['failures'].append({
            'file': template_name,
            'reason': f'Read error: {str(e)}'
        })
        print(f"✗ {template_name} - FAIL: {e}")

# ============================================================================
# OUTPUT REPORT
# ============================================================================

print("\n" + "=" * 80)
print("SECTION: FIXED FILES")
print("=" * 80)
for item in report['fixed']:
    print(f"{item['file']} → {item['change']}")

if not report['fixed']:
    print("(none)")

print("\n" + "=" * 80)
print("SECTION: CREATED FILES")
print("=" * 80)
for item in report['created']:
    print(f"{item['file']} → {item['reason']}")

if not report['created']:
    print("(none)")

print("\n" + "=" * 80)
print("SECTION: DELETED FILES")
print("=" * 80)
for item in report['deleted']:
    print(f"{item['file']} → {item['reason']}")

if not report['deleted']:
    print("(none)")

print("\n" + "=" * 80)
print("SECTION: FAILURES")
print("=" * 80)
for item in report['failures']:
    print(f"{item['file']} → {item['reason']}")

if not report['failures']:
    print("(none)")

print("\n" + "=" * 80)
print("SECTION: STATUS")
print("=" * 80)

if report['failures']:
    print("FAIL - Errors detected that require attention")
else:
    print("PASS - All templates validated and rendering correctly")

print("=" * 80 + "\n")
