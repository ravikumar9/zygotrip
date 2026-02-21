from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone
from datetime import datetime
from apps.accounts.selectors import user_has_role
from .models import Booking, BookingStatusHistory, BookingGuest, BookingPriceBreakdown
from .forms import BookingCreateForm
from apps.payments.services import process_payment
from apps.wallet.services import get_or_create_wallet
from apps.hotels.models import Property


def _get_booking_or_403(user, uuid):
	booking = get_object_or_404(Booking, uuid=uuid, is_active=True)
	if booking.user != user:
		raise PermissionDenied
	return booking


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
	property_obj = get_object_or_404(Property, id=property_id)
	
	if request.method == 'POST':
		form = BookingCreateForm(request.POST, property_obj=property_obj)
		if form.is_valid():
			# Create booking in PENDING status
			check_in = form.cleaned_data['check_in']
			check_out = form.cleaned_data['check_out']
			quantity = form.cleaned_data.get('quantity', 1)
			
			# Calculate nights
			nights = (check_out - check_in).days
			if nights <= 0:
				messages.error(request, 'Check-out date must be after check-in date.')
				return render(request, 'booking/create.html', {
					'form': form,
					'property': property_obj
				})
			
			# Calculate base price
			base_price = property_obj.base_price * nights * quantity if property_obj.base_price else 0
			
			# Collect guest details from form
			guest_name = form.cleaned_data.get('guest_full_name', request.user.full_name)
			guest_email = form.cleaned_data.get('guest_email', request.user.email)
			guest_phone = form.cleaned_data.get('guest_phone', '')
			
			# Create booking with guest details
			booking = Booking.objects.create(
				user=request.user,
				property=property_obj,
				check_in=check_in,
				check_out=check_out,
				total_amount=base_price,
				status=Booking.STATUS_REVIEW,
				guest_name=guest_name,
				guest_email=guest_email,
				guest_phone=guest_phone
			)
			
			# Calculate total with tax
			tax_amount = base_price * 0.05  # 5% GST
			total_with_tax = base_price + tax_amount
			
			# Create price breakdown
			BookingPriceBreakdown.objects.create(
				booking=booking,
				base_amount=base_price,
				meal_amount=0,
				service_fee=0,
				gst=tax_amount,
				promo_discount=0,
				total_amount=total_with_tax
			)
			
			# Update booking total
			booking.total_amount = total_with_tax
			booking.save(update_fields=['total_amount'])
			
			# Record booking status
			BookingStatusHistory.objects.create(
				booking=booking,
				status=Booking.STATUS_REVIEW,
				note='Booking created'
			)
			
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


@login_required
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


@login_required
def success(request, uuid):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	booking = _get_booking_or_403(request.user, uuid)
	if booking.status != Booking.STATUS_CONFIRMED:
		raise PermissionDenied
	return render(request, 'booking/success.html', {'booking': booking})


@login_required
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