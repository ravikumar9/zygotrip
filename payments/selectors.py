from .models import Invoice


def invoices_for_user(user):
    return Invoice.objects.filter(booking__user=user, is_active=True).select_related('booking', 'booking__property')
