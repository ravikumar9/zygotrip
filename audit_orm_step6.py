#!/usr/bin/env python
"""
STEP 6: Run queries audit
Verify ORM queries execute without errors
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Property
from django.db.models import Count, Min, Q

print("=" * 70)
print("STEP 6: ORM QUERIES AUDIT")
print("=" * 70)

# Test 1: Basic count
try:
    count = Property.objects.count()
    print(f"\n✓ Property.objects.count() = {count}")
except Exception as e:
    print(f"\n✗ FAILED: Property.objects.count()")
    print(f"  Error: {e}")
    exit(1)

# Test 2: First object
try:
    first = Property.objects.first()
    if first:
        print(f"✓ First property: {first.name}")
        print(f"  - ID: {first.id}")
        print(f"  - City: {first.city_text}")
        print(f"  - Type: {first.property_type}")
        print(f"  - Rating: {first.rating}")
    else:
        print("✓ No properties in database (OK)")
except Exception as e:
    print(f"\n✗ FAILED: Property.objects.first()")
    print(f"  Error: {e}")
    exit(1)

# Test 3: Filter query
try:
    filtered = Property.objects.filter(property_type='Hotel').count()
    print(f"\n✓ Property.objects.filter(property_type='Hotel').count() = {filtered}")
except Exception as e:
    print(f"\n✗ FAILED: filter(property_type='Hotel')")
    print(f"  Error: {e}")
    exit(1)

# Test 4: Annotate query
try:
    annotated = Property.objects.annotate(total=Count('id')).first()
    print(f"✓ Property.objects.annotate(total=Count('id')) = {annotated}")
except Exception as e:
    print(f"\n✗ FAILED: annotate(total=Count('id'))")
    print(f"  Error: {e}")
    exit(1)

# Test 5: Related lookups
try:
    by_owner = Property.objects.filter(owner__isnull=False).count()
    print(f"\n✓ Property.objects.filter(owner__isnull=False).count() = {by_owner}")
except Exception as e:
    print(f"\n✗ FAILED: filter(owner__isnull=False)")
    print(f"  Error: {e}")
    exit(1)

# Test 6: Q objects
try:
    q_result = Property.objects.filter(
        Q(property_type='Hotel') | Q(property_type='Guesthouse')
    ).count()
    print(f"✓ Property.objects.filter(Q(...) | Q(...)).count() = {q_result}")
except Exception as e:
    print(f"\n✗ FAILED: filter with Q objects")
    print(f"  Error: {e}")
    exit(1)

# Test 7: Prefetch
try:
    props = Property.objects.prefetch_related('images').first()
    print(f"\n✓ Property.objects.prefetch_related('images') = OK")
except Exception as e:
    print(f"\n✗ FAILED: prefetch_related('images')")
    print(f"  Error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✅ ORM AUDIT PASSED - All queryset operations work")
print("=" * 70)