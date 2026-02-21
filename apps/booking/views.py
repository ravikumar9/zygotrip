from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from datetime import datetime
from apps.accounts.selectors import user_has_role
from .forms import BookingCreateForm
from apps.payments.services import process_payment
from apps.wallet.services import get_or_create_wallet
from .selectors import get_booking_or_403, get_property_or_404
from .services import create_simple_booking, transition_booking_status


@login_required
def create(request, property_id):
	"""
	Create a new booking and redirect to review.
	GET: Show booking form with hotel details
	POST: Create booking and go to review
	"""
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	
	# Get property
	property_obj = get_property_or_404(property_id)
	
	if request.method == 'POST':
		form = BookingCreateForm(request.POST, property_obj=property_obj)
		if form.is_valid():
			try:
				booking = create_simple_booking(request.user, property_obj, form)
			except ValueError:
				messages.error(request, 'Check-out date must be after check-in date.')
				return render(request, 'booking/create.html', {
					'form': form,
					'property': property_obj,
				})
			messages.success(request, 'Booking created. Please review and confirm.')
			return redirect('booking:review', uuid=booking.uuid)
	else:
		form = BookingCreateForm(property_obj=property_obj)
	
	return render(request, 'booking/create.html', {
		'form': form,
		'property': property_obj
	})


@login_required
def review(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = get_booking_or_403(request.user, uuid)
	if booking.status not in [booking.STATUS_REVIEW, booking.STATUS_PAYMENT]:
		raise PermissionDenied
	if request.method == 'POST':
		transition_booking_status(booking, booking.STATUS_PAYMENT)
		return redirect('booking:payment', uuid=booking.uuid)
	nights = (booking.check_out - booking.check_in).days
	return render(request, 'booking/review.html', {'booking': booking, 'nights': nights})


@login_required
def payment(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = get_booking_or_403(request.user, uuid)
	if booking.status != booking.STATUS_PAYMENT:
		raise PermissionDenied
	if request.method == 'POST':
		use_wallet = request.POST.get('use_wallet') == 'on'
		process_payment(booking, use_wallet=use_wallet)
		messages.success(request, 'Payment successful.')
		return redirect('booking:success', uuid=booking.uuid)
	wallet = get_or_create_wallet(request.user)
	return render(request, 'booking/payment.html', {'booking': booking, 'wallet': wallet})


@login_required
def success(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = get_booking_or_403(request.user, uuid)
	if booking.status != booking.STATUS_CONFIRMED:
		raise PermissionDenied
	return render(request, 'booking/success.html', {'booking': booking})


@login_required
@require_http_methods(["POST"])
def cancel(request, uuid):
	"""API endpoint to cancel booking (called when timer expires)"""
	if not user_has_role(request.user, 'customer'):
		return JsonResponse({'error': 'Unauthorized'}, status=403)
	
	try:
		booking = get_booking_or_403(request.user, uuid)
	except PermissionError:
		return JsonResponse({'error': 'Booking not found'}, status=404)
	
	# Only cancel if still in review or payment status
	if booking.status in [booking.STATUS_REVIEW, booking.STATUS_PAYMENT]:
		transition_booking_status(booking, booking.STATUS_CANCELLED, note='Cancelled due to timer expiry')
		return JsonResponse({'success': True, 'message': 'Booking cancelled'})
	
	return JsonResponse({'error': 'Cannot cancel booking'}, status=400)

# Create your views here.