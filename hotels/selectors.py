from dashboard_admin.models import PropertyApproval
from .models import Property


def public_properties():
    return Property.objects.filter(
        is_active=True,
        approval__status=PropertyApproval.STATUS_APPROVED,
        approval__is_active=True,
    ).select_related('approval')


def owner_properties(owner):
    return Property.objects.filter(owner=owner, is_active=True)
