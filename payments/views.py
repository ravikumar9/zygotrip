from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from accounts.selectors import user_has_role
from accounts.permissions import login_required_403
from .models import Invoice


@login_required_403
def invoice(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	invoice_obj = get_object_or_404(Invoice, uuid=uuid, is_active=True)
	if invoice_obj.booking.user != request.user:
		raise PermissionDenied
	return render(request, 'payments/invoice.html', {'invoice': invoice_obj})

# Create your views here.
