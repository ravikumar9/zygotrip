from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from accounts.selectors import user_has_role
from accounts.permissions import login_required_403
from .models import Booking, BookingStatusHistory
from payments.services import process_payment
from wallet.services import get_or_create_wallet


def _get_booking_or_403(user, uuid):
	booking = get_object_or_404(Booking, uuid=uuid, is_active=True)
	if booking.user != user:
		raise PermissionDenied
	return booking


@login_required_403
def review(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = _get_booking_or_403(request.user, uuid)
	if booking.status not in [Booking.STATUS_REVIEW, Booking.STATUS_PAYMENT]:
		raise PermissionDenied
	if request.method == 'POST':
		booking.status = Booking.STATUS_PAYMENT
		booking.save(update_fields=['status', 'updated_at'])
		BookingStatusHistory.objects.create(booking=booking, status=Booking.STATUS_PAYMENT)
		return redirect('booking:payment', uuid=booking.uuid)
	nights = (booking.check_out - booking.check_in).days
	return render(request, 'booking/review.html', {'booking': booking, 'nights': nights})


@login_required_403
def payment(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = _get_booking_or_403(request.user, uuid)
	if booking.status != Booking.STATUS_PAYMENT:
		raise PermissionDenied
	if request.method == 'POST':
		use_wallet = request.POST.get('use_wallet') == 'on'
		process_payment(booking, use_wallet=use_wallet)
		messages.success(request, 'Payment successful.')
		return redirect('booking:success', uuid=booking.uuid)
	wallet = get_or_create_wallet(request.user)
	return render(request, 'booking/payment.html', {'booking': booking, 'wallet': wallet})


@login_required_403
def success(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = _get_booking_or_403(request.user, uuid)
	if booking.status != Booking.STATUS_CONFIRMED:
		raise PermissionDenied
	return render(request, 'booking/success.html', {'booking': booking})


@login_required_403
@require_http_methods(["POST"])
def cancel(request, uuid):
	"""API endpoint to cancel booking (called when timer expires)"""
	if not user_has_role(request.user, 'customer'):
		return JsonResponse({'error': 'Unauthorized'}, status=403)
	
	try:
		booking = _get_booking_or_403(request.user, uuid)
	except PermissionDenied:
		return JsonResponse({'error': 'Booking not found'}, status=404)
	
	# Only cancel if still in review or payment status
	if booking.status in [Booking.STATUS_REVIEW, Booking.STATUS_PAYMENT]:
		booking.status = Booking.STATUS_CANCELLED
		booking.save(update_fields=['status', 'updated_at'])
		BookingStatusHistory.objects.create(booking=booking, status=Booking.STATUS_CANCELLED, note='Cancelled due to timer expiry')
		return JsonResponse({'success': True, 'message': 'Booking cancelled'})
	
	return JsonResponse({'error': 'Cannot cancel booking'}, status=400)

# Create your views here.
