"""
Unified Search Engine - Main Orchestrator
Production-grade OTA search with ranking, caching, and fallback strategies
"""

from typing import Dict, Any, Optional, List
from django.db.models import Q, QuerySet, Prefetch
from django.core.exceptions import ObjectDoesNotExist
import time
import logging

from .query_parser import QueryParser, QueryIntent
from .ranking_engine import RankingEngine
from .autocomplete_engine import AutocompleteEngine
from .filters_engine import FiltersEngine
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class UnifiedSearchEngine:
    """
    Main search orchestrator with intelligent fallback strategies
    
    Features:
    ─────────
    - Intent-based search routing
    - Multi-level fallback (exact → fuzzy → partial → popular)
    - Intelligent ranking with relevance scoring
    - Smart caching with Redis
    - Performance tracking (<120ms target)
    - Grouped autocomplete results
    """
    
    def __init__(self, cache_ttl: int = 900):
        self.query_parser = QueryParser()
        self.ranking_engine = RankingEngine()
        self.autocomplete_engine = AutocompleteEngine()
        self.filters_engine = FiltersEngine()
        self.cache_manager = CacheManager()
        self.cache_ttl = cache_ttl
    
    def search_hotels(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Main search method with fallback strategies
        
        Args:
            query: Search query string
            filters: Optional filter parameters
            use_cache: Whether to use cache (default: True)
            
        Returns:
            {
                "results": [...],  # Property queryset or list
                "count": 42,
                "query_time_ms": 85,
                "strategy": "fuzzy",
                "intent": "city"
            }
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if use_cache:
                cached = self.cache_manager.get_search_results(query, filters)
                if cached is not None:
                    cached['cached'] = True
                    return cached
            
            # Parse query intent
            intent = self.query_parser.parse(query)
            logger.info(f"Search query: '{query}' → Intent: {intent.type} (confidence: {intent.confidence})")
            
            # Get base queryset
            from apps.hotels.models import Property
            queryset = Property.objects.select_related(
                'city', 'locality'
            ).prefetch_related(
                'images', 'amenities', 'rooms'
            ).filter(is_active=True)
            
            # Apply search based on intent
            queryset = self._apply_search_strategy(queryset, intent)
            
            # Apply filters if provided
            if filters:
                queryset = self.filters_engine.apply_filters(queryset, filters)
            
            # Apply ranking
            queryset = self.ranking_engine.rank_results(queryset, query)
            
            # Get result count
            count = queryset.count()
            
            # Fallback if no results
            if count == 0:
                queryset = self._fallback_search(query, filters)
                count = queryset.count()
            
            # Prepare response
            query_time = (time.time() - start_time) * 1000  # Convert to ms
            
            result = {
                "results": queryset,
                "count": count,
                "query_time_ms": round(query_time, 2),
                "strategy": self.query_parser.get_search_strategy(intent),
                "intent": intent.type,
                "cached": False
            }
            
            # Cache results
            if use_cache and count > 0:
                self.cache_manager.set_search_results(query, result, filters)
            
            logger.info(f"Search completed: {count} results in {query_time:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return {
                "results": Property.objects.none(),
                "count": 0,
                "error": str(e),
                "query_time_ms": (time.time() - start_time) * 1000
            }
    
    def _apply_search_strategy(self, queryset: QuerySet, intent: QueryIntent) -> QuerySet:
        """
        Apply search based on detected intent
        
        Strategies:
        ───────────
        - hotel_id: Exact ID match
        - city: City name match
        - locality: Locality + city match
        - property: Property name match
        - landmark: Landmark proximity (fallback to property name)
        - unknown: Broad search across all fields
        """
        try:
            if intent.type == 'hotel_id':
                # Exact ID match
                return queryset.filter(id=int(intent.tokens[0]))
            
            elif intent.type == 'city':
                # City name match
                city_name = intent.normalized
                return queryset.filter(
                    Q(city__name__icontains=city_name) |
                    Q(city__name__istartswith=city_name) |
                    Q(city__name__iexact=city_name)
                )
            
            elif intent.type == 'locality':
                # Locality and city match
                tokens = intent.tokens
                if len(tokens) >= 2:
                    locality_name = tokens[0]
                    city_name = tokens[-1]
                    return queryset.filter(
                        Q(locality__name__icontains=locality_name) &
                        Q(city__name__icontains=city_name)
                    )
                else:
                    return queryset.filter(locality__name__icontains=intent.normalized)
            
            elif intent.type == 'property':
                # Property name match
                return queryset.filter(
                    Q(name__icontains=intent.normalized) |
                    Q(name__istartswith=intent.normalized)
                )
            
            elif intent.type == 'landmark':
                # Search near landmarks (fallback to name search)
                # Note: Implement geospatial search if coordinates available
                return queryset.filter(
                    Q(name__icontains=intent.normalized) |
                    Q(description__icontains=intent.normalized) |
                    Q(locality__name__icontains=intent.normalized)
                )
            
            else:
                # Unknown intent: broad search
                return self._broad_search(queryset, intent.normalized)
        
        except Exception as e:
            logger.error(f"Search strategy error: {e}")
            return queryset
    
    def _broad_search(self, queryset: QuerySet, query: str) -> QuerySet:
        """
        Broad search across multiple fields
        Used for unknown intent or fallback
        """
        return queryset.filter(
            Q(name__icontains=query) |
            Q(city__name__icontains=query) |
            Q(locality__name__icontains=query) |
            Q(description__icontains=query)
        )
    
    def _fallback_search(self, query: str, filters: Optional[Dict] = None) -> QuerySet:
        """
        Fallback strategy when no results found
        
        Fallback Chain:
        ───────────────
        1. Fuzzy match (relaxed query)
        2. Partial word match (any token)
        3. City-only match
        4. Popular properties in any city
        """
        from apps.hotels.models import Property
        
        logger.info(f"Triggering fallback for query: '{query}'")
        
        # Try partial token match
        tokens = query.lower().split()
        if len(tokens) > 1:
            for token in tokens:
                if len(token) >= 3:
                    results = Property.objects.filter(
                        Q(name__icontains=token) |
                        Q(city__name__icontains=token),
                        is_active=True
                    )
                    if results.exists():
                        logger.info(f"Fallback success: partial match on '{token}'")
                        return results
        
        # Try city-only (remove all filters except city)
        if filters and filters.get('city_id'):
            results = Property.objects.filter(
                city_id=filters['city_id'],
                is_active=True
            )
            if results.exists():
                logger.info("Fallback success: city-only match")
                return results
        
        # Last resort: popular properties
        logger.info("Fallback: returning popular properties")
        return Property.objects.filter(
            is_active=True
        ).order_by('-search_score', '-rating')[:20]
    
    def autocomplete(self, query: str) -> Dict[str, Any]:
        """
        Autocomplete with grouped results
        
        Args:
            query: Partial search query
            
        Returns:
            Grouped autocomplete results
        """
        start_time = time.time()
        
        try:
            # Check cache
            cached = self.cache_manager.get_autocomplete_results(query)
            if cached is not None:
                logger.debug(f"Autocomplete cache hit: '{query}'")
                return cached
            
            # Get autocomplete results
            results = self.autocomplete_engine.autocomplete(query)
            
            # Add timing
            query_time = (time.time() - start_time) * 1000
            results['query_time_ms'] = round(query_time, 2)
            
            # Cache results
            self.cache_manager.set_autocomplete_results(query, results)
            
            logger.info(f"Autocomplete: '{query}' → {sum(len(g['items']) for g in results.get('groups', []))} results in {query_time:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"Autocomplete error: {e}")
            return {"groups": [], "error": str(e)}
    
    def get_filters(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Get available filter options
        
        Args:
            query: Optional base query to scope filters
            
        Returns:
            Available filter options with counts
        """
        try:
            # Check cache
            cached = self.cache_manager.get_filters()
            if cached is not None:
                return cached
            
            # Get base queryset
            from apps.hotels.models import Property
            queryset = Property.objects.filter(is_active=True)
            
            # Scope to query if provided
            if query:
                intent = self.query_parser.parse(query)
                queryset = self._apply_search_strategy(queryset, intent)
            
            # Get filter options
            filters = self.filters_engine.get_available_filters(queryset)
            
            # Cache filters
            self.cache_manager.set_filters(filters)
            
            return filters
            
        except Exception as e:
            logger.error(f"Get filters error: {e}")
            return {}
    
    def get_popular_destinations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get popular destinations for homepage/empty state
        
        Args:
            limit: Number of destinations to return
            
        Returns:
            List of popular cities with property counts
        """
        try:
            from apps.core.models import City
            from django.db.models import Count
            
            cities = City.objects.annotate(
                property_count=Count('property', distinct=True)
            ).filter(
                property_count__gt=0
            ).order_by('-property_count')[:limit]
            
            return [
                {
                    "name": city.name,
                    "id": city.id,
                    "slug": city.slug if hasattr(city, 'slug') else city.name.lower().replace(' ', '-'),
                    "property_count": city.property_count,
                    "image": city.image.url if hasattr(city, 'image') and city.image else None
                }
                for city in cities
            ]
            
        except Exception as e:
            logger.error(f"Popular destinations error: {e}")
            return []


# Create a singleton instance of the search engine
search_engine = UnifiedSearchEngine()