from django.contrib import admin
from core.location_models import Country, State, City, Locality, LocationSearchIndex, RegionGroup

# Import marketplace admin registrations
from .marketplace_admin import (
    DestinationAdmin,
    CategoryAdmin,
    OfferAdmin,
    SearchIndexAdmin
)


# Location hierarchy admin
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_active',)


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'country', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('country', 'is_active')
    raw_id_fields = ('country',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'state', 'hotel_count', 'popularity_score', 'is_top_destination')
    search_fields = ('name', 'code', 'alternate_names')
    list_filter = ('state', 'is_top_destination', 'is_active')
    raw_id_fields = ('state',)
    list_editable = ('popularity_score', 'is_top_destination')


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'locality_type', 'hotel_count', 'popularity_score')
    search_fields = ('name', 'landmarks')
    list_filter = ('city', 'locality_type', 'is_active')
    raw_id_fields = ('city',)


@admin.register(RegionGroup)
class RegionGroupAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_popular', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('is_popular', 'is_active')
    filter_horizontal = ('cities',)

