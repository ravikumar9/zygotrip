"""Update property-locality links and refresh hotel counts"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip_project.settings')
django.setup()

from apps.hotels.models import Property
from apps.core.location_models import Locality
from django.db.models import Count

def update_property_localities():
    """Link properties to localities based on area field"""
    props = Property.objects.filter(status='approved').select_related('city')
    updated_count = 0
    
    for prop in props:
        if not prop.area:
            continue
            
        area_lower = prop.area.lower().strip()
        
        # Try exact match first
        locality = Locality.objects.filter(
            name__iexact=prop.area,
            city=prop.city
        ).first()
        
        # Try partial match
        if not locality:
            locality = Locality.objects.filter(
                name__icontains=prop.area.split()[0],
                city=prop.city
            ).first()
        
        if locality:
            prop.locality = locality
            prop.save(update_fields=['locality'])
            updated_count += 1
            print(f"✓ {prop.name} → {locality.name}, {locality.city.name}")
    
    print(f"\nUpdated {updated_count} properties with locality links")
    
    # Update hotel counts on localities
    for locality in Locality.objects.all():
        count = Property.objects.filter(
            locality=locality,
            status='approved',
            agreement_signed=True
        ).count()
        locality.hotel_count = count
        locality.save(update_fields=['hotel_count'])
    
    print(f"✓ Updated hotel counts on all localities")
    
    # Show results
    print("\n=== Locality Counts (Coorg) ===")
    coorg_localities = Locality.objects.filter(
        city__code='COORG',
        hotel_count__gt=0
    ).values('name', 'hotel_count', 'city__name')
    
    for loc in coorg_localities:
        print(f"{loc['name']}, {loc['city__name']}: {loc['hotel_count']} properties")

if __name__ == '__main__':
    update_property_localities()
