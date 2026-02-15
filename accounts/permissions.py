from functools import wraps
from django.core.exceptions import PermissionDenied
from .selectors import user_has_role


def login_required_403(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
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


class RoleRequiredMixin:
    required_role = None

    def dispatch(self, request, *args, **kwargs):
        if self.required_role and not user_has_role(request.user, self.required_role):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
