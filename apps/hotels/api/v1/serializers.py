"""
DRF Serializers for Hotel API v1.

Response contract:
  All list endpoints return:
  {
      "success": true,
      "data": {
          "results": [...],
          "pagination": { "count": N, "next": "url|null", "previous": "url|null" }
      }
  }

  All detail endpoints return:
  {
      "success": true,
      "data": { ... }
  }

  All errors return (via drf_exception_handler):
  {
      "success": false,
      "error": { "code": "...", "message": "...", "detail": null|{} }
  }
"""
from rest_framework import serializers
from apps.hotels.models import Property, PropertyImage, PropertyAmenity, RatingAggregate
from apps.rooms.models import RoomType


class PropertyImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyImage
        fields = ['id', 'url', 'caption', 'is_featured', 'display_order']

    def get_url(self, obj):
        return obj.resolved_url


class PropertyAmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyAmenity
        fields = ['name', 'icon']


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'description', 'capacity', 'max_occupancy',
            'bed_type', 'meal_plan', 'base_price', 'available_count',
        ]


class PropertyCardSerializer(serializers.ModelSerializer):
    """
    Compact serializer for listing cards.
    Uses pre-annotated fields (min_room_price, avg_rating) — zero extra queries.
    """
    city_name = serializers.CharField(source='city.name', default='')
    min_price = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    amenity_names = serializers.SerializerMethodField()
    rating_tier = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'slug', 'name', 'property_type',
            'city_name', 'area', 'landmark', 'address',
            'latitude', 'longitude',
            'rating', 'review_count', 'star_category',
            'min_price',
            'primary_image',
            'amenity_names',
            'rating_tier',
            'has_free_cancellation',
            'is_trending',
            'bookings_today',
        ]

    def get_min_price(self, obj):
        # Always use annotation — never call .base_price property in a list
        val = getattr(obj, 'min_room_price', None)
        return int(val) if val else 0

    def get_primary_image(self, obj):
        # Uses prefetch cache — no extra query
        images = list(obj.images.all())
        img = next((i for i in images if i.is_featured), None) or (images[0] if images else None)
        return img.resolved_url if img else ''

    def get_amenity_names(self, obj):
        # Uses prefetch cache — no extra query
        return [a.name for a in obj.amenities.all()]

    def get_rating_tier(self, obj):
        rating = float(obj.rating or 0)
        if rating >= 4.5:
            return 'excellent'
        if rating >= 3.5:
            return 'good'
        if rating >= 2.5:
            return 'average'
        return 'below_average'


class PropertyDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for property detail page.
    Includes rooms, images gallery, amenities, rating breakdown.
    """
    city_name = serializers.CharField(source='city.name', default='')
    locality_name = serializers.CharField(source='locality.name', default='')
    min_price = serializers.SerializerMethodField()
    images = PropertyImageSerializer(many=True, read_only=True)
    amenities = PropertyAmenitySerializer(many=True, read_only=True)
    room_types = RoomTypeSerializer(many=True, read_only=True)
    rating_tier = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'slug', 'name', 'property_type', 'description',
            'city_name', 'locality_name', 'area', 'landmark', 'address', 'country',
            'latitude', 'longitude',
            'rating', 'review_count', 'star_category',
            'min_price',
            'rating_tier',
            'has_free_cancellation', 'cancellation_hours',
            'is_trending', 'bookings_today',
            'images', 'amenities', 'room_types',
        ]

    def get_min_price(self, obj):
        val = getattr(obj, 'min_room_price', None) or obj.base_price
        return int(val) if val else 0

    def get_rating_tier(self, obj):
        rating = float(obj.rating or 0)
        if rating >= 4.5:
            return 'excellent'
        if rating >= 3.5:
            return 'good'
        return 'average'
