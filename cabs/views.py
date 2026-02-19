from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.permissions import provider_required
from django.db import transaction
from django.db.models import Q, F, DecimalField, Prefetch
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from promos.models import Promo
from .models import Cab, CabBooking, CabImage, CabAvailability
from .forms import CabRegistrationForm, CabFilterForm, CabBookingForm
from .serializers import CabRenderReadySerializer


def cab_list(request):
	"""
	Cab listing with server-side filtering
	"""
	cabs = Cab.objects.filter(is_active=True).select_related('owner').prefetch_related('images').order_by('-created_at')

	# Search
	search_query = request.GET.get('q', '') or ''
	if search_query:
		cabs = cabs.filter(Q(name__icontains=search_query))

	# City filter
	selected_cities = request.GET.getlist('city') or []
	if selected_cities:
		cabs = cabs.filter(city__in=selected_cities)

	# Seats filter
	selected_seats = request.GET.getlist('seats') or []
	if selected_seats:
		try:
			selected_seats = [int(s) for s in selected_seats]
			cabs = cabs.filter(seats__in=selected_seats)
		except (ValueError, TypeError):
			selected_seats = []

	# Fuel type filter
	selected_fuels = request.GET.getlist('fuel_type') or []
	if selected_fuels:
		cabs = cabs.filter(fuel_type__in=selected_fuels)

	# Price filter
	max_price = request.GET.get('max_price') or ''
	min_price = request.GET.get('min_price') or ''
	try:
		from decimal import InvalidOperation
		if max_price:
			max_price_val = Decimal(str(max_price).strip())
			cabs = cabs.filter(system_price_per_km__lte=max_price_val)
		if min_price:
			min_price_val = Decimal(str(min_price).strip())
			cabs = cabs.filter(system_price_per_km__gte=min_price_val)
	except (ValueError, TypeError, InvalidOperation):
		max_price = ''
		min_price = ''

	# Sorting
	sort_by = request.GET.get('sort', '').strip()
	if sort_by == 'price_low':
		cabs = cabs.order_by('system_price_per_km')
	elif sort_by == 'price_high':
		cabs = cabs.order_by('-system_price_per_km')
	elif sort_by == 'seats':
		cabs = cabs.order_by('-seats')
	else:
		cabs = cabs.order_by('-created_at')

	# Pagination
	paginator = Paginator(cabs, 20)
	page = request.GET.get('page') or 1
	try:
		page_num = int(page)
		if page_num < 1:
			page_num = 1
		page_obj = paginator.get_page(page_num)
	except (ValueError, TypeError):
		page_obj = paginator.get_page(1)

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
			'total_results': paginator.count,
		},
		'page_title': 'Cabs - Zygotrip',
		'empty_state': len(cards) == 0,
	}
	return render(request, 'cabs/list.html', context)


def cab_detail(request, cab_id):
	"""
	Cab detail page with availability and booking
	"""
	cab = get_object_or_404(Cab, id=cab_id, is_active=True)
	images = cab.images.all()
	availability = cab.availability.filter(date__gte=timezone.now().date()).order_by('date')[:30]
	
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
	cab = get_object_or_404(Cab, id=cab_id, is_active=True)
	best_coupon = None

	def _get_best_coupon():
		try:
			now = timezone.now().date()
			coupons = Promo.objects.filter(
				is_active=True,
				applicable_module__in=['cabs', 'all'],
				starts_at__lte=now,
				ends_at__gte=now
			).order_by('-value')[:1]
			return coupons.first()
		except Exception:
			return None
	
	if request.method == 'POST':
		form = CabBookingForm(request.POST)
		if form.is_valid():
			with transaction.atomic():
				booking = form.save(commit=False)
				booking.cab = cab
				booking.user = request.user
				booking.booking_date = form.cleaned_data['booking_date']
				booking.price_per_km = cab.system_price_per_km
				booking.base_fare = 50
				
				availability, _ = CabAvailability.objects.select_for_update().get_or_create(
					cab=cab,
					date=booking.booking_date,
					defaults={'is_available': True},
				)
				if not availability.is_available:
					messages.error(request, 'Cab is not available for the selected date.')
					return redirect('cabs:booking', cab_id=cab.id)
				
				# Calculate total before discount
				booking.calculate_total()
				
				# Apply coupon if provided
				promo_code = form.cleaned_data.get('promo_code', '').strip().upper()
				if promo_code:
					try:
						promo = Promo.objects.get(
							code=promo_code,
							is_active=True,
							applicable_module__in=['cabs', 'all']
						)
						now = timezone.now().date()
						if not promo.starts_at or promo.starts_at <= now:
							if not promo.ends_at or promo.ends_at >= now:
								# Apply discount
								if promo.discount_type == 'percent':
									discount = (booking.total_price * Decimal(promo.value)) / Decimal(100)
								else:
									discount = Decimal(promo.value)
								
								# Cap discount at max_discount if set
								if promo.max_discount:
									discount = min(discount, Decimal(promo.max_discount))
								
								booking.discount_amount = discount
								booking.promo_code = promo_code
								booking.final_price = booking.total_price - discount
							else:
								messages.warning(request, f'Promo code "{promo_code}" has expired')
						else:
							messages.warning(request, f'Promo code "{promo_code}" is not valid yet')
					except Promo.DoesNotExist:
						messages.warning(request, f'Promo code "{promo_code}" not found or invalid for cabs')
				
				booking.save()
				availability.is_available = False
				availability.save(update_fields=['is_available', 'updated_at'])
			messages.success(request, 'Booking confirmed! Check your bookings.')
			return redirect('cabs:booking-success', booking_id=booking.id)
		best_coupon = _get_best_coupon()
	else:
		form = CabBookingForm()
		# Auto-suggest best coupon for cabs
		best_coupon = _get_best_coupon()
	
	context = {
		'cab': cab,
		'form': form,
		'best_coupon': best_coupon,
	}
	return render(request, 'cabs/booking.html', context)


def booking_success(request, booking_id):
	"""Booking confirmation page"""
	booking = get_object_or_404(CabBooking, id=booking_id)
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
			with transaction.atomic():
				cab = form.save(commit=False)
				cab.owner = request.user
				# Auto-calculate system_price_per_km
				from django.conf import settings
				margin = getattr(settings, 'PLATFORM_CAB_MARGIN', 3)
				cab.system_price_per_km = cab.base_price_per_km + Decimal(margin)
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
	cabs = Cab.objects.filter(owner=request.user).prefetch_related('images', 'bookings')
	
	context = {'cabs': cabs}
	return render(request, 'cabs/owner_list.html', context)


@login_required
def owner_cab_edit(request, cab_id):
	"""
	Owner edit cab details
	"""
	cab = get_object_or_404(Cab, id=cab_id, owner=request.user)
	
	if request.method == 'POST':
		with transaction.atomic():
			cab = Cab.objects.select_for_update().get(id=cab_id, owner=request.user)
			form = CabRegistrationForm(request.POST, instance=cab)
			if form.is_valid():
				cab = form.save(commit=False)
				from django.conf import settings
				margin = getattr(settings, 'PLATFORM_CAB_MARGIN', 3)
				cab.system_price_per_km = cab.base_price_per_km + Decimal(margin)
				cab.save()
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
	cab = get_object_or_404(Cab, id=cab_id, owner=request.user)
	
	if request.method == 'POST':
		with transaction.atomic():
			cab = Cab.objects.select_for_update().get(id=cab_id, owner=request.user)
			cab.is_active = False
			cab.save()
		messages.success(request, 'Cab deleted successfully!')
		return redirect('cabs:owner-list')
	
	context = {'cab': cab}
	return render(request, 'cabs/owner_delete.html', context)


def coming_soon(request):
	context = {'module_name': 'Cabs'}
	return render(request, 'coming_soon.html', context)

