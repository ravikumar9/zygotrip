# Re-export from apps.hotels for backwards compatibility
from apps.hotels.models import (
    Property,
    PropertyImage,
    PropertyOffer,
    RatingAggregate,
    Category,
    PropertyCategory,
    PropertyPolicy,
    PropertyAmenity,
)

__all__ = [
    'Property',
    'PropertyImage',
    'PropertyOffer',
    'RatingAggregate',
    'Category',
    'PropertyCategory',
    'PropertyPolicy',
    'PropertyAmenity',
]
