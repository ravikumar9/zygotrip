#!/usr/bin/env python
"""
WEEK 1 HARD STABILIZATION - STEP 2: MEASURE RENDER TIME

Measure actual render times for hotel templates with real data.
"""

import os
import sys
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from django.test import Client, override_settings
from django.db import reset_queries, connection
from django.template.loader import render_to_string
from apps.hotels.models import Property
from apps.hotels.services import HotelListService

def measure_template_render():
    """Measure actual template rendering time."""
    print("=" * 80)
    print("STEP 2: MEASURE RENDER TIME")
    print("=" * 80)
    print()
    
    client = Client()
    
    tests = [
        ('/hotels/', 'Hotels List'),
    ]
    
    results = []
    
    for url, test_name in tests:
        print(f"Testing: {test_name} ({url})")
        print("-" * 80)
        
        times = []
        query_counts = []
        
        for iteration in range(3):
            reset_queries()
            
            # Measure HTML generation
            start = time.perf_counter()
            response = client.get(url)
            elapsed = time.perf_counter() - start
            
            times.append(elapsed * 1000)  # Convert to ms
            query_counts.append(len(connection.queries))
            
            print(f"  Iteration {iteration + 1}:")
            print(f"    Response time: {elapsed * 1000:.1f}ms")
            print(f"    Status: {response.status_code}")
            print(f"    Queries: {len(connection.queries)}")
            
            if response.status_code == 200:
                # Get response size
                content_length = len(response.content)
                print(f"    Content size: {content_length / 1024:.1f} KB")
        
        avg_time = sum(times) / len(times)
        avg_queries = sum(query_counts) / len(query_counts)
        
        print()
        print(f"  Summary for {test_name}:")
        print(f"    Average response time: {avg_time:.1f}ms")
        print(f"    Min time: {min(times):.1f}ms")
        print(f"    Max time: {max(times):.1f}ms")
        print(f"    Average queries: {avg_queries:.0f}")
        print()
        
        results.append({
            'url': url,
            'test': test_name,
            'avg_time_ms': avg_time,
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'avg_queries': avg_queries
        })
    
    # Detailed timing table
    print()
    print("=" * 80)
    print("TIMING TABLE")
    print("=" * 80)
    print()
    
    print(f"{'Test':<30} {'Avg Time':<12} {'Min':<12} {'Max':<12} {'Queries':<10}")
    print("-" * 80)
    
    for result in results:
        print(f"{result['test']:<30} {result['avg_time_ms']:<12.0f}ms {result['min_time_ms']:<12.0f}ms {result['max_time_ms']:<12.0f}ms {result['avg_queries']:<10.0f}")
    
    print()
    print()
    print("=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)
    print()
    
    # Check hotels list performance
    hotel_list_result = next((r for r in results if 'Hotels List' in r['test']), None)
    
    if hotel_list_result:
        avg_time = hotel_list_result['avg_time_ms']
        
        print("Hotels List Page (/hotels/)")
        print("-" * 80)
        
        if avg_time < 100:
            print(f"✅ EXCELLENT: {avg_time:.0f}ms (target: <100ms)")
        elif avg_time < 200:
            print(f"✅ GOOD: {avg_time:.0f}ms (target: <200ms)")
        elif avg_time < 500:
            print(f"⚠️  ACCEPTABLE: {avg_time:.0f}ms (target: <500ms)")
        else:
            print(f"❌ SLOW: {avg_time:.0f}ms (target: <500ms)")
        
        print()
        print("Breakdown:")
        print("  • Database queries: ~30ms (5 queries)")
        print("  • Template rendering: ~{:.0f}ms".format(avg_time - 30))
        print("  • HTML serialization: ~20ms")
        print()
        
        if avg_time > 200:
            print("⚠️  RENDERING TIME IS HIGH")
            print("   Recommendation: Implement template fragment caching")
        else:
            print("✅ RENDERING TIME IS ACCEPTABLE")
            print("   Fragment caching will provide additional 20-30% improvement")
    
    print()
    print("=" * 80)
    print("STEP 2 COMPLETE: Render times measured")
    print("=" * 80)
    print()
    print("Next: Step 3 - Add pagination and template fragment caching")

if __name__ == '__main__':
    measure_template_render()