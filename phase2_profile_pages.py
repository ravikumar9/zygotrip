"""
PHASE 2 - Query Profiler Script
Profile top 5 pages and identify N+1 issues, slow queries, duplicates
"""
import os
import django
import time
from collections import Counter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client
from django.db import reset_queries, connection
from django.conf import settings

# Enable query logging
settings.DEBUG = True

client = Client()

# Pages to profile
pages = [
    ("/hotels/", "Hotels Listing"),
    ("/search/?q=hotel", "Search Page"),
    ("/packages/", "Packages Page"),
    ("/cabs/", "Cabs Page"),
    ("/", "Homepage"),
]

results = {}

print("\n" + "="*80)
print("PHASE 2: TOP 5 PAGES QUERY PROFILING")
print("="*80)

for url, name in pages:
    print(f"\n📊 Profiling: {name} ({url})")
    print("-" * 80)
    
    # Reset queries before each test
    reset_queries()
    
    try:
        start = time.time()
        response = client.get(url)
        elapsed = time.time() - start
        
        queries = connection.queries
        query_count = len(queries)
        
        # Find duplicates
        query_patterns = [q['sql'].split('WHERE')[0] if 'WHERE' in q['sql'] else q['sql'] for q in queries]
        duplicates = [item for item, count in Counter(query_patterns).items() if count > 1]
        
        # Find slow queries (>50ms)
        slow_queries = [q for q in queries if float(q.get('time', 0)) > 0.05]
        
        # Find potential N+1 patterns (duplicate SELECT queries)
        select_queries = [q['sql'] for q in queries if q['sql'].strip().startswith('SELECT')]
        duplicate_selects = Counter(select_queries)
        n_plus_one = {sql: count for sql, count in duplicate_selects.items() if count > 1}
        
        results[name] = {
            'url': url,
            'status': response.status_code,
            'time': elapsed,
            'query_count': query_count,
            'duplicate_count': len(duplicates),
            'slow_query_count': len(slow_queries),
            'n_plus_one_count': len(n_plus_one),
            'slow_queries': slow_queries,
            'n_plus_one': n_plus_one,
        }
        
        print(f"  ✅ Status: {response.status_code}")
        print(f"  ⏱️  Response Time: {elapsed*1000:.2f}ms")
        print(f"  📈 Total Queries: {query_count}")
        print(f"  🔄 Duplicate Query Patterns: {len(duplicates)}")
        print(f"  🐌 Slow Queries (>50ms): {len(slow_queries)}")
        print(f"  🔁 Potential N+1: {len(n_plus_one)} patterns")
        
        # Show N+1 details if any
        if n_plus_one:
            print(f"\n  N+1 Details:")
            for sql, count in list(n_plus_one.items())[:3]:
                sql_short = sql[:70] + "..." if len(sql) > 70 else sql
                print(f"    - {count}x: {sql_short}")
        
        # Show slow queries if any
        if slow_queries:
            print(f"\n  Slow Queries:")
            for q in slow_queries[:3]:
                time_ms = float(q.get('time', 0)) * 1000
                sql_short = q['sql'][:70] + "..." if len(q['sql']) > 70 else q['sql']
                print(f"    - {time_ms:.2f}ms: {sql_short}")
        
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
        results[name] = {'error': str(e)}

# Generate report
print("\n\n" + "="*80)
print("SUMMARY TABLE")
print("="*80 + "\n")

print(f"{'Page':<25} {'Queries':<10} {'Dups':<8} {'Slow':<8} {'N+1':<10}")
print("-" * 80)

for name, data in results.items():
    if 'error' not in data:
        q_count = data['query_count']
        dup = data['duplicate_count']
        slow = data['slow_query_count']
        n1 = data['n_plus_one_count']
        
        # Color code
        q_color = "🔴" if q_count > 15 else "🟡" if q_count > 10 else "🟢"
        
        print(f"{name:<25} {q_count:<10}{q_color} {dup:<8} {slow:<8} {n1:<10}")

print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)

# Calculate totals
total_queries = sum(r.get('query_count', 0) for r in results.values())
total_slow = sum(r.get('slow_query_count', 0) for r in results.values())
total_n1 = sum(r.get('n_plus_one_count', 0) for r in results.values())

print(f"\n✅ Total Queries Across 5 Pages: {total_queries}")
print(f"🐌 Total Slow Queries (>50ms): {total_slow}")
print(f"🔁 Total N+1 Issues: {total_n1}")

# Recommendations
print("\n📋 RECOMMENDATIONS")
print("-" * 80)

if total_queries > 50:
    print("\n🔴 CRITICAL: Total queries too high (target: <50)")
    print("   → Need: More select_related/prefetch_related")
else:
    print("\n🟡 MEDIUM: Check individual pages")

if total_n1 > 5:
    print(f"\n🔴 CRITICAL: {total_n1} N+1 issues found")
    print("   → See details above for affected tables")
else:
    print(f"\n🟢 GOOD: Only {total_n1} N+1 issues")

if total_slow > 3:
    print(f"\n🔴 CRITICAL: {total_slow} slow queries found")
    print("   → Need: Database indexes or query optimization")
else:
    print(f"\n🟢 GOOD: Only {total_slow} slow queries")

print("\n" + "="*80)
print("NEXT PHASE: Fix N+1 queries with select_related/prefetch_related")
print("="*80 + "\n")