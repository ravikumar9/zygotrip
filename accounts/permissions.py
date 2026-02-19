from functools import wraps
from django.core.exceptions import PermissionDenied
from .selectors import user_has_role


def login_required_403(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request.user, 'is_authenticated') or not request.user.is_authenticated:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


def role_required(role_code):
    def decorator(view_func):
        @login_required_403
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not user_has_role(request.user, role_code):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


def provider_required(view_func):
    """
    Decorator for provider creation routes
    Allows users with any of these roles: property_owner, bus_operator, cab_provider, package_provider
    """
    @login_required_403
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        allowed_roles = ['property_owner', 'bus_operator', 'cab_provider', 'package_provider']
        has_provider_role = any(user_has_role(request.user, role) for role in allowed_roles)
        if not has_provider_role:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped


class RoleRequiredMixin:
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if self.required_role and not user_has_role(request.user, self.required_role):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
