# PHASE 6: Global Search Engine with Relevance Scoring
# File: apps/search/services/global_search.py

from django.db.models import Q, Case, When, Value, IntegerField
from hotels.models import Property
import logging

logger = logging.getLogger(__name__)


class GlobalSearchService:
    """
    Search across all properties with relevance scoring.
    
    Scoring System:
    +10 points: Property name match
    +5 points:  City match  
    +3 points:  Area/district match
    +2 points:  Landmark match
    """
    
    SCORE_NAME = 10
    SCORE_CITY = 5
    SCORE_AREA = 3
    SCORE_LANDMARK = 2
    
    @staticmethod
    def search(query, limit=50):
        """Search properties by query with relevance ranking."""
        if not query or len(query.strip()) < 2:
            return Property.objects.none()
        
        query = query.strip()
        
        # Build query with relevance scoring
        search_query = Q()
        
        # Base queries
        by_name = Q(name__icontains=query)
        by_city = Q(city__icontains=query)
        by_area = Q(area__icontains=query)
        by_landmark = Q(landmarks__icontains=query)
        
        # Get all matching properties
        results = Property.objects.filter(
            by_name | by_city | by_area | by_landmark
        ).distinct()
        
        if not results.exists():
            logger.info(f"No properties found for query: {query}")
            return Property.objects.none()
        
        # Apply relevance scoring
        results = results.annotate(
            search_score=Case(
                # Primary match: name (highest priority)
                When(name__icontains=query, then=Value(self.SCORE_NAME)),
                # Secondary: city
                When(city__icontains=query, then=Value(self.SCORE_CITY)),
                # Tertiary: area
                When(area__icontains=query, then=Value(self.SCORE_AREA)),
                # Quaternary: landmark
                When(landmarks__icontains=query, then=Value(self.SCORE_LANDMARK)),
                output_field=IntegerField(),
                default=Value(0)
            )
        )
        
        # Sort by relevance (highest score first)
        results = results.order_by('-search_score', 'name')
        
        logger.info(f"Found {results.count()} properties for query: {query}")
        return results[:limit]
    
    @staticmethod
    def search_by_city(city, limit=50):
        """Search properties by city."""
        results = Property.objects.filter(city__icontains=city)
        return results.order_by('name')[:limit]
    
    @staticmethod  
    def search_by_area(area, limit=50):
        """Search properties by area/district."""
        results = Property.objects.filter(area__icontains=area)
        return results.order_by('name')[:limit]
    
    @staticmethod
    def search_by_landmark(landmark, limit=50):
        """Search properties by nearby landmark."""
        results = Property.objects.filter(landmarks__icontains=landmark)
        return results.order_by('name')[:limit]
    
    @staticmethod
    def advanced_search(filters):
        """
        Advanced search with multiple filters.
        
        Usage:
        filters = {
            'query': 'Taj Mahal',
            'city': 'Agra',
            'min_price': 2000,
            'max_price': 5000,
            'rating_min': 4.0,
        }
        results = GlobalSearchService.advanced_search(filters)
        """
        results = Property.objects.all()
        
        # Text search (most important)
        if filters.get('query'):
            query = filters['query']
            results = results.filter(
                Q(name__icontains=query) |
                Q(city__icontains=query) |
                Q(area__icontains=query) |
                Q(landmarks__icontains=query)
            )
        
        # City filter
        if filters.get('city'):
            results = results.filter(city__icontains=filters['city'])
        
        # Area filter
        if filters.get('area'):
            results = results.filter(area__icontains=filters['area'])
        
        # Price filters (if model has price field)
        if filters.get('min_price'):
            results = results.filter(base_price__gte=filters['min_price'])
        
        if filters.get('max_price'):
            results = results.filter(base_price__lte=filters['max_price'])
        
        # Rating filter (if aggregates exist)
        if filters.get('rating_min'):
            results = results.filter(
                rating_aggregate__average_rating__gte=filters['rating_min']
            )
        
        return results.distinct().order_by('-rating_aggregate__average_rating', 'name')
