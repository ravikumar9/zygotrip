# No models in search app - uses other app models
class SearchResult:
    """
    Unified search result object (Step 5: HARD STABILIZATION).
    Replaces tuple returns from search operations.
    Provides consistent interface across all search domains.
    
    Usage:
        result = SearchResult(
            result_id=1,
            title="Hotel Name",
            description="Description",
            result_type='hotel',
            price=5000,
            rating=4.5
        )
    """
    
    def __init__(self, result_id, title, description, result_type, 
                 price=None, rating=None, location=None, details=None, metadata=None):
        self.id = result_id
        self.title = title
        self.description = description
        self.type = result_type  # 'hotel', 'package', 'bus', 'cab', etc.
        self.price = price
        self.rating = rating
        self.location = location
        self.details = details or {}
        self.metadata = metadata or {}
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'price': self.price,
            'rating': self.rating,
            'location': self.location,
            'details': self.details,
            'metadata': self.metadata,
        }
    
    def to_json(self):
        """Serialize to JSON-compatible dict."""
        import json
        return json.dumps(self.to_dict())
    
    def __repr__(self):
        return f"<SearchResult: {self.type} | {self.title}>"
    
    def __str__(self):
        return f"{self.title} ({self.type})"
    
    @classmethod
    def from_hotel(cls, hotel_obj):
        """Create SearchResult from Hotel model."""
        return cls(
            result_id=hotel_obj.id,
            title=hotel_obj.name,
            description=hotel_obj.description[:200] if hotel_obj.description else '',
            result_type='hotel',
            price=float(hotel_obj.base_price) if hotel_obj.base_price else None,
            rating=float(hotel_obj.rating) if hotel_obj.rating else None,
            location=getattr(hotel_obj.city, 'name', None),
            details={
                'property_type': hotel_obj.property_type,
                'address': hotel_obj.address,
            },
            metadata={
                'slug': hotel_obj.slug,
                'images': list(hotel_obj.images.values_list('image_url', flat=True))[:3],
            }
        )