from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.core.location_models import City, Locality
from apps.hotels.models import Property
from apps.search.models import SearchIndex


class Command(BaseCommand):
    help = "Rebuild unified SearchIndex entries for autocomplete"

    def handle(self, *args, **options):
        SearchIndex.objects.all().delete()

        city_entries = []
        for city in City.objects.filter(is_active=True):
            name = city.display_name or city.name
            city_entries.append(
                SearchIndex(
                    name=name,
                    type=SearchIndex.TYPE_CITY,
                    property_count=city.hotel_count,
                    slug=slugify(name),
                )
            )

        area_entries = []
        for locality in Locality.objects.filter(is_active=True):
            name = locality.display_name or locality.name
            area_entries.append(
                SearchIndex(
                    name=name,
                    type=SearchIndex.TYPE_AREA,
                    property_count=locality.hotel_count,
                    slug=slugify(name),
                )
            )

        property_entries = []
        for prop in Property.objects.filter(is_active=True):
            slug = prop.slug or slugify(prop.name)
            property_entries.append(
                SearchIndex(
                    name=prop.name,
                    type=SearchIndex.TYPE_PROPERTY,
                    property_count=None,
                    slug=slug,
                )
            )

        SearchIndex.objects.bulk_create(city_entries, ignore_conflicts=True)
        SearchIndex.objects.bulk_create(area_entries, ignore_conflicts=True)
        SearchIndex.objects.bulk_create(property_entries, ignore_conflicts=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"SearchIndex rebuilt: cities={len(city_entries)}, areas={len(area_entries)}, properties={len(property_entries)}"
            )
        )
