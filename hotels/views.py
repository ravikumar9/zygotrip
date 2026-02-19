import json
import logging
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.shortcuts import redirect, render
from django.utils import timezone
from accounts.models import Role, User, UserRole
from accounts.selectors import user_has_role
from core.date_utils import get_date_for_template
from booking.forms import BookingCreateForm
from booking.services import create_booking
from dashboard_admin.models import PropertyApproval
from apps.hotels.serializers import RenderReadySerializer
from .models import Property
from .selectors import public_properties

logger = logging.getLogger(__name__)


def hotel_list(request):
	try:
		# Optimize queries with proper prefetch and select_related
		properties = public_properties().select_related(
			'rating_breakdown'
		).prefetch_related(
			'amenities', 
			'images', 
			'offers',
			'room_types__images',
			'meal_plans'
		).annotate(
			min_room_price=Min('room_types__base_price'),
			review_count=Count('reviews', distinct=True),
		)

		search_query = request.GET.get('q', '').strip()
		selected_cities = [city.strip() for city in request.GET.getlist('city') if city.strip()]
		selected_ratings = [rating.strip() for rating in request.GET.getlist('rating') if rating.strip()]
		selected_amenities = [amenity.strip() for amenity in request.GET.getlist('amenities') if amenity.strip()]
		min_price = request.GET.get('min_price') or ''
		max_price = request.GET.get('max_price') or ''

		if search_query:
			properties = properties.filter(name__icontains=search_query)

		if selected_cities:
			city_query = Q()
			for city in selected_cities:
				city_query |= Q(city__iexact=city)
			properties = properties.filter(city_query)

		if selected_ratings:
			try:
				rating_thresholds = [Decimal(value) for value in selected_ratings]
				min_rating = min(rating_thresholds)
				properties = properties.filter(rating__gte=min_rating)
			except (InvalidOperation, ValueError):
				pass

		if min_price:
			try:
				properties = properties.filter(base_price__gte=Decimal(min_price))
			except (InvalidOperation, ValueError):
				pass

		if max_price:
			try:
				properties = properties.filter(base_price__lte=Decimal(max_price))
			except (InvalidOperation, ValueError):
				pass

		if selected_amenities:
			amenity_map = {
				'wifi': 'Free WiFi',
				'breakfast': 'Breakfast Included',
				'pool': 'Pool',
				'parking': 'Parking',
			}
			amenity_names = [amenity_map.get(value, value) for value in selected_amenities]
			properties = properties.filter(amenities__name__in=amenity_names).distinct()

		# Add pagination (20 per page)
		paginator = Paginator(properties, 20)
		page = request.GET.get('page') or 1
		try:
			page_num = int(page)
			if page_num < 1:
				page_num = 1
			page_obj = paginator.get_page(page_num)
		except (ValueError, TypeError):
			page_obj = paginator.get_page(1)
		pagination_query = request.GET.copy()
		if 'page' in pagination_query:
			pagination_query.pop('page')

		# Serialize cards using RenderReadySerializer
		cards = RenderReadySerializer.serialize_listing_cards(page_obj.object_list)

		context = {
			'page_obj': page_obj,
			'cards': cards,
			'selected_cities': selected_cities,
			'selected_ratings': selected_ratings,
			'selected_amenities': selected_amenities,
			'min_price': min_price or '',
			'max_price': max_price or '',
			'search_query': search_query,
			'pagination_query': pagination_query.urlencode(),
		}
		return render(request, 'hotels/list.html', context)
		
	except Exception as e:
		logger.exception("HOTEL_LIST_CRASH: %s", str(e))
		messages.error(request, "An error occurred while loading hotels. Please try again.")
		return render(request, 'hotels/list.html', {
			'page_obj': None,
			'cards': [],
			'error_message': 'Failed to load hotels',
		})


def hotel_detail(request, pk):
	property_obj = Property.objects.filter(
		pk=pk,
		is_active=True,
		approval__status=PropertyApproval.STATUS_APPROVED,
	).first()
	if not property_obj:
		return render(request, 'hotels/not_found.html', status=200)
	form = BookingCreateForm(request.POST or None, property_obj=property_obj)
	if request.method == 'POST':
		if form.is_valid():
			booking_user = request.user
			if not request.user.is_authenticated:
				guest_email = form.cleaned_data['guest_email']
				if not guest_email:
					form.add_error('guest_email', 'Email is required for guest booking.')
					messages.error(request, 'Please provide an email to continue as guest.')
					return render(
						request,
						'hotels/detail.html',
						{
							'property': property_obj,
							'form': form,
							'room_prices_json': json.dumps({}),
							'meal_prices_json': json.dumps({}),
							'today': get_date_for_template(),  # Min date for date inputs
						},
					)
				booking_user, created = User.objects.get_or_create(
					email=guest_email,
					defaults={'full_name': form.cleaned_data['guest_full_name']},
				)
				if created:
					booking_user.set_unusable_password()
					booking_user.save(update_fields=['password', 'updated_at'])
				role = Role.objects.get(code='customer')
				UserRole.objects.get_or_create(user=booking_user, role=role)
				login(request, booking_user, backend='django.contrib.auth.backends.ModelBackend')
			elif not user_has_role(request.user, 'customer'):
				raise PermissionDenied
			booking = create_booking(
				user=booking_user,
				property_obj=property_obj,
				room_type=form.cleaned_data['room_type'],
				quantity=form.cleaned_data['quantity'],
				meal_plan=form.cleaned_data['meal_plan'],
				check_in=form.cleaned_data['check_in'],
				check_out=form.cleaned_data['check_out'],
				guests=[{
					'full_name': form.cleaned_data['guest_full_name'],
					'age': form.cleaned_data['guest_age'],
					'email': form.cleaned_data['guest_email'],
				}],
				promo_code=form.cleaned_data['promo_code'],
			)
			messages.success(request, 'Booking created. Review and confirm payment.')
			return redirect('booking:review', uuid=booking.uuid)
		messages.error(request, 'Please fix the booking form errors.')
	room_prices = {room.id: str(room.base_price) for room in property_obj.room_types.all()}
	meal_prices = {meal.id: str(meal.price) for meal in property_obj.meal_plans.all()}
	context = {
		'property': property_obj,
		'form': form,
		'room_prices_json': json.dumps(room_prices),
		'meal_prices_json': json.dumps(meal_prices),
		'today': get_date_for_template(),  # Min date for date inputs
	}
	return render(request, 'hotels/detail.html', context)

# Create your views here.
