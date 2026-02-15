from django.db.models import Q
from .models import Permission, RolePermission, UserRole


def user_has_role(user, role_code):
    if not user.is_authenticated:
        return False
    return UserRole.objects.filter(user=user, role__code=role_code, is_active=True, role__is_active=True).exists()


def user_has_permission(user, permission_code):
    if not user.is_authenticated:
        return False
    return RolePermission.objects.filter(
        role__userrole__user=user,
        permission__code=permission_code,
        is_active=True,
        role__is_active=True,
        permission__is_active=True,
    ).exists()
