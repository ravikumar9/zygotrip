from django.db import transaction
from dashboard_admin.models import PropertyApproval
from .models import Property


def create_property(owner, **data):
    property_obj = Property.objects.create(owner=owner, **data)
    PropertyApproval.objects.create(property=property_obj)
    return property_obj


def submit_property_for_approval(property_obj):
    with transaction.atomic():
        approval = property_obj.approval
        approval.status = PropertyApproval.STATUS_PENDING
        approval.save(update_fields=['status', 'updated_at'])
    return approval
