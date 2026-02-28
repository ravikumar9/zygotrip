"""
PHASE 8: Autosuggest Hardening
Response format: {cities: [{name, count}], areas: [{name, count}], properties: [{name, slug}]}
Must show counts like Goibibo
"""
from django.db.models import Count
from apps.hotels.models import Property
import logging

logger = logging.getLogger(__name__)


class AutosuggestService:
    """Provides search suggestions with counts (like Goibibo)"""
    
    @staticmethod
    def get_suggestions(query_string, limit=10):
        """
        Get autosuggest results for query.
        
        Returns:
            {
                'query': str,
                'cities': [{'name': str, 'count': int}, ...],
                'areas': [{'name': str, 'count': int}, ...],
                'properties': [{'name': str, 'slug': str, 'city': str}, ...],
            }
        """
        if not query_string or len(query_string) < 2:
            return {
                'query': query_string,
                'cities': [],
                'areas': [],
                'properties': [],
                'message': 'Query too short (min 2 chars)'
            }
        
        query = query_string.strip().lower()
        
        # Get approved properties only
        approved_properties = Property.objects.filter(
            status='approved',
            agreement_signed=True
        )
        
        # Get matching cities with counts
        cities = AutosuggestService._get_matching_cities(
            query, approved_properties, limit
        )
        
        # Get matching areas with counts
        areas = AutosuggestService._get_matching_areas(
            query, approved_properties, limit
        )
        
        # Get matching properties
        properties = AutosuggestService._get_matching_properties(
            query, approved_properties, limit
        )
        
        return {
            'query': query_string,
            'cities': cities,
            'areas': areas,
            'properties': properties,
        }
    
    @staticmethod
    def _get_matching_cities(query, approved_properties, limit):
        """
        Get distinct cities matching query with property count.
        
        Returns: [{'name': str, 'state': str, 'code': str, 'count': int, 'latitude': float, 'longitude': float}, ...]
        """
        try:
            from apps.core.models import City
            from django.db.models import Q, Count as DjangoCount
            
            # Search cities by name or alternate names
            cities = City.objects.filter(
                Q(name__icontains=query) | Q(alternate_names__icontains=query),
                is_active=True
            ).select_related('state').annotate(
                property_count=DjangoCount('hotels')
            ).order_by('-property_count', '-popularity_score')[:limit]
            
            return [
                {
                    'name': city.name,
                    'state': city.state.name,
                    'code': city.code,
                    'count': city.property_count,
                    'latitude': float(city.latitude),
                    'longitude': float(city.longitude),
                    'type': 'city',
                    'display': f"{city.name}, {city.state.name} ({city.property_count} properties)"
                }
                for city in cities
            ]
        
        except Exception as e:
            logger.error(f"Error getting cities: {str(e)}")
            return []
    
    @staticmethod
    def _get_matching_areas(query, approved_properties, limit):
        """
        Get distinct areas (localities) matching query with property count.
        
        Returns: [{'name': str, 'city': str, 'count': int, 'latitude': float, 'longitude': float}, ...]
        """
        try:
            from apps.core.models import Locality
            from django.db.models import Q, Count as DjangoCount
            
            # Search localities by name or landmarks
            localities = Locality.objects.filter(
                Q(name__icontains=query) | Q(landmarks__icontains=query),
                is_active=True
            ).select_related('city__state').annotate(
                property_count=DjangoCount('hotels')
            ).order_by('-property_count', '-popularity_score')[:limit]
            
            return [
                {
                    'name': locality.name,
                    'city': locality.city.name,
                    'state': locality.city.state.name,
                    'count': locality.property_count,
                    'latitude': float(locality.latitude),
                    'longitude': float(locality.longitude),
                    'type': 'area',
                    'display': f"{locality.name}, {locality.city.name} ({locality.property_count} properties)"
                }
                for locality in localities
            ]
        
        except Exception as e:
            logger.warning(f"Error getting areas: {str(e)}")
            return []
    
    @staticmethod
    def _get_matching_properties(query, approved_properties, limit):
        """
        Get distinct properties matching query.
        
        Returns: [{'name': str, 'slug': str, 'city': str, 'state': str, 'latitude': float, 'longitude': float}, ...]
        """
        try:
            properties = approved_properties.filter(
                name__icontains=query
            ).select_related('city__state').values(
                'id', 'name', 'slug', 'city__name', 'city__state__name', 'latitude', 'longitude'
            )[:limit]
            
            return [
                {
                    'name': prop['name'],
                    'slug': prop['slug'],
                    'city': prop['city__name'],
                    'state': prop['city__state__name'],
                    'latitude': float(prop['latitude']),
                    'longitude': float(prop['longitude']),
                    'type': 'property',
                    'display': f"{prop['name']} - {prop['city__name']}"
                }
                for prop in properties
            ]
        
        except Exception as e:
            logger.error(f"Error getting properties: {str(e)}")
            return []
            logger.error(f"Error getting properties: {str(e)}")
            return []
    
    @staticmethod
    def get_popular_destinations(limit=10):
        """
        Get most popular destinations (by property count).
        Shown in UI when user hasn't typed anything.
        
        Returns: [{'name': str, 'count': int, 'type': 'city'}, ...]
        """
        try:
            approved = Property.objects.filter(
                status='approved',
                agreement_signed=True
            )
            
            cities = approved.values('location').annotate(
                count=Count('id')
            ).order_by('-count')[:limit]
            
            return [
                {
                    'name': city['location'],
                    'count': city['count'],
                    'type': 'city'
                }
                for city in cities
            ]
        
        except Exception as e:
            logger.error(f"Error getting popular destinations: {str(e)}")
            return []
    
    @staticmethod
    def get_trending_searches(limit=5):
        """
        Get trending searches (would require logging searches).
        For now, returns most-booked properties.
        
        Returns: [{'name': str, 'slug': str}, ...]
        """
        try:
            # Could integrate with search logging in future
            approved = Property.objects.filter(
                status='approved',
                agreement_signed=True
            ).order_by('-rating')[:limit]
            
            return [
                {
                    'name': prop.name,
                    'slug': prop.slug,
                }
                for prop in approved
            ]
        
        except Exception as e:
            logger.error(f"Error getting trending: {str(e)}")
            return []
