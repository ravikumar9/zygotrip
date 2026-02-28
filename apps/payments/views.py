from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import json

from apps.accounts.selectors import user_has_role
from apps.booking.selectors import get_booking_or_403
from .selectors import InvoiceDTO
from .services import handle_payment_webhook


@login_required
def invoice_detail(request, invoice_uuid):
	if not user_has_role(request.user, "customer"):
		raise PermissionDenied
	booking = get_booking_or_403(request.user, invoice_uuid)
	invoice = InvoiceDTO(
		booking=booking,
		status="paid",
		issued_at=booking.updated_at or booking.created_at,
	)
	return render(request, "payments/invoice.html", {"invoice": invoice})


@csrf_exempt  # Payment gateways can't send CSRF tokens
@require_POST
def payment_webhook(request):
	"""
	Idempotent payment gateway webhook handler.
	
	Expected payload:
	{
		"payment_reference_id": "gateway-txn-123",
		"status": "success|failed|pending",
		"amount": 10000.00,
		"...": "other gateway data"
	}
	"""
	try:
		payload = json.loads(request.body)
	except json.JSONDecodeError:
		return JsonResponse(
			{'error': 'Invalid JSON'},
			status=400
		)
	
	try:
		result = handle_payment_webhook(
			payment_reference_id=payload.get('payment_reference_id'),
			status=payload.get('status'),
			amount=payload.get('amount'),
			**payload
		)
		return JsonResponse(result, status=200)
	
	except ValidationError as e:
		return JsonResponse(
			{'error': str(e)},
			status=400
		)
	except Exception as e:
		from django.conf import settings
		if settings.DEBUG:
			raise
		# Log but don't expose internal errors
		return JsonResponse(
			{'error': 'Webhook processing failed'},
			status=500
		)

