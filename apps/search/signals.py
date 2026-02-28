from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.text import slugify

from apps.core.location_models import City, Locality
from apps.hotels.models import Property

from .models import SearchIndex


def _upsert_index(entry_type, name, slug, property_count=None):
    if not name:
        return
    SearchIndex.objects.update_or_create(
        type=entry_type,
        slug=slug,
        defaults={
            "name": name,
            "property_count": property_count,
            "is_active": True,
        },
    )


@receiver(post_save, sender=City)
def index_city(sender, instance, **kwargs):
    if not instance.is_active:
        return
    _upsert_index(
        SearchIndex.TYPE_CITY,
        instance.display_name or instance.name,
        slugify(instance.display_name or instance.name),
        property_count=instance.hotel_count,
    )


@receiver(post_save, sender=Locality)
def index_area(sender, instance, **kwargs):
    if not instance.is_active:
        return
    _upsert_index(
        SearchIndex.TYPE_AREA,
        instance.display_name or instance.name,
        slugify(instance.display_name or instance.name),
        property_count=instance.hotel_count,
    )


@receiver(post_save, sender=Property)
def index_property(sender, instance, **kwargs):
    if not instance.is_active:
        return
    slug = instance.slug or slugify(instance.name)
    _upsert_index(
        SearchIndex.TYPE_PROPERTY,
        instance.name,
        slug,
        property_count=None,
    )
