from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.permissions import provider_required
from django.utils import timezone
from decimal import Decimal
from .forms import CabRegistrationForm, CabFilterForm, CabBookingForm
from .serializers import CabRenderReadySerializer
from .selectors import (
	get_cab_queryset,
	paginate_cabs,
	get_cab_or_404,
	get_owner_cab_or_404,
	get_owner_cabs,
	get_cab_booking_or_404,
	get_cab_availability,
)
from .services import get_best_coupon, create_cab_booking, set_system_price, update_cab_details, deactivate_cab


def cab_list(request):
	"""
	Cab listing with server-side filtering
	"""
	# Search
	search_query = request.GET.get('q', '') or ''

	# City filter
	selected_cities = request.GET.getlist('city') or []
	if selected_cities:
		cabs = cabs.filter(city__in=selected_cities)

	# Seats filter
	selected_seats = request.GET.getlist('seats') or []
	if selected_seats:
		try:
			selected_seats = [int(s) for s in selected_seats]
		except (ValueError, TypeError):
			selected_seats = []

	# Fuel type filter
	selected_fuels = request.GET.getlist('fuel_type') or []

	# Price filter
	max_price = request.GET.get('max_price') or ''
	min_price = request.GET.get('min_price') or ''
	max_price_val = None
	min_price_val = None
	try:
		from decimal import InvalidOperation
		if max_price:
			max_price_val = Decimal(str(max_price).strip())
		if min_price:
			min_price_val = Decimal(str(min_price).strip())
	except (ValueError, TypeError, InvalidOperation):
		max_price = ''
		min_price = ''
		max_price_val = None
		min_price_val = None

	# Sorting
	sort_by = request.GET.get('sort', '').strip()
	filters = {
		'search_query': search_query,
		'selected_cities': selected_cities,
		'selected_seats': selected_seats,
		'selected_fuels': selected_fuels,
		'max_price_val': max_price_val,
		'min_price_val': min_price_val,
		'sort_by': sort_by,
	}
	cabs = get_cab_queryset(filters)

	# Pagination
	page = request.GET.get('page') or 1
	page_obj = paginate_cabs(cabs, page)

	# Apply data contract serialization
	cards = CabRenderReadySerializer.serialize_listing_cards(page_obj.object_list)

	context = {
		'page_obj': page_obj,
		'cards': cards,
		'cabs': list(page_obj.object_list),
		'form': CabFilterForm(),
		'_test_marker': 'CAB_LIST_VIEW_MODIFIED_SUCCESS_12345',
		'filter_labels': ['Vehicle Type', 'Seating Capacity', 'Price Range'],
		'filters': {
			'search_query': search_query,
			'selected_cities': selected_cities,
			'selected_seats': selected_seats,
			'selected_fuels': selected_fuels,
			'max_price': max_price or '500',
			'min_price': min_price or '0',
			'sort_by': sort_by,
		},
		'pagination': {
			'page_obj': page_obj,
			'page': page_obj.number,
			'num_pages': page_obj.paginator.num_pages,
			'has_previous': page_obj.has_previous(),
			'has_next': page_obj.has_next(),
			'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
			'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
		},
		'meta': {
			'total_results': page_obj.paginator.count,
		},
		'page_title': 'Cabs - Zygotrip',
		'empty_state': len(cards) == 0,
	}
	return render(request, 'cabs/list.html', context)


def cab_detail(request, cab_id):
	"""
	Cab detail page with availability and booking
	"""
	cab = get_cab_or_404(cab_id)
	images = cab.images.all()
	availability = get_cab_availability(cab)
	
	context = {
		'cab': cab,
		'images': images,
		'availability': availability,
	}
	return render(request, 'cabs/detail.html', context)


@login_required
def cab_booking(request, cab_id):
	"""
	Cab booking with pricing calculation and coupon application
	"""
	cab = get_cab_or_404(cab_id)
	best_coupon = None
	
	if request.method == 'POST':
		form = CabBookingForm(request.POST)
		if form.is_valid():
			promo_code = form.cleaned_data.get('promo_code', '').strip().upper()
			booking, applied_promo = create_cab_booking(request.user, cab, form, promo_code)
			if booking is None:
				messages.error(request, 'Cab is not available for the selected date.')
				return redirect('cabs:booking', cab_id=cab.id)
			if promo_code and applied_promo is None:
				messages.warning(request, f'Promo code "{promo_code}" not found or invalid for cabs')
			messages.success(request, 'Booking confirmed! Check your bookings.')
			return redirect('cabs:booking-success', booking_id=booking.id)
		best_coupon = get_best_coupon()
	else:
		form = CabBookingForm()
		# Auto-suggest best coupon for cabs
		best_coupon = get_best_coupon()
	
	context = {
		'cab': cab,
		'form': form,
		'best_coupon': best_coupon,
	}
	return render(request, 'cabs/booking.html', context)


def booking_success(request, booking_id):
	"""Booking confirmation page"""
	booking = get_cab_booking_or_404(booking_id)
	if booking.user != request.user:
		messages.error(request, 'Unauthorized')
		return redirect('cabs:list')
	
	context = {'booking': booking}
	return render(request, 'cabs/booking_success.html', context)


@provider_required
def owner_cab_add(request):
	"""
	Owner registration form for adding new cabs
	"""
	# Check if user is owner (has owner role or permission)
	if request.method == 'POST':
		form = CabRegistrationForm(request.POST)
		if form.is_valid():
			cab = form.save(commit=False)
			cab.owner = request.user
			set_system_price(cab)
			cab.save()
			messages.success(request, 'Cab registered successfully!')
			return redirect('cabs:owner-list')
	else:
		form = CabRegistrationForm()
	
	context = {'form': form}
	return render(request, 'cabs/owner_registration.html', context)


@login_required
def owner_cab_list(request):
	"""
	Owner dashboard - list own cabs
	"""
	cabs = get_owner_cabs(request.user)
	
	context = {'cabs': cabs}
	return render(request, 'cabs/owner_list.html', context)


@login_required
def owner_cab_edit(request, cab_id):
	"""
	Owner edit cab details
	"""
	cab = get_owner_cab_or_404(cab_id, request.user)
	
	if request.method == 'POST':
		form = CabRegistrationForm(request.POST, instance=cab)
		if form.is_valid():
			update_cab_details(cab_id, request.user, form)
			messages.success(request, 'Cab updated successfully!')
			return redirect('cabs:owner-list')
	else:
		form = CabRegistrationForm(instance=cab)
	
	context = {'form': form, 'cab': cab}
	return render(request, 'cabs/owner_edit.html', context)


@login_required
def owner_cab_delete(request, cab_id):
	"""
	Owner delete cab (soft delete via is_active flag)
	"""
	cab = get_owner_cab_or_404(cab_id, request.user)
	
	if request.method == 'POST':
		deactivate_cab(cab_id, request.user)
		messages.success(request, 'Cab deleted successfully!')
		return redirect('cabs:owner-list')
	
	context = {'cab': cab}
	return render(request, 'cabs/owner_delete.html', context)


def coming_soon(request):
	context = {'module_name': 'Cabs'}
	return render(request, 'coming_soon.html', context)