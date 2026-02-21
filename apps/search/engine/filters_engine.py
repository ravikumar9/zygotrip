"""Stub Filters Engine for search filters."""


class FiltersEngine:
    """Stub FiltersEngine class for applying search filters."""

    def __init__(self):
        pass

    def apply_filters(self, queryset, filters=None):
        """Apply filters to a queryset."""
        if filters is None:
            filters = {}
        return queryset

    def get_available_filters(self, queryset):
        """Get available filters for a queryset."""
        return {}




