import json
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from accounts.models import Role, User, UserRole
from accounts.selectors import user_has_role
from booking.forms import BookingCreateForm
from booking.services import create_booking
from dashboard_admin.models import PropertyApproval
from .models import Property
from .selectors import public_properties


def hotel_list(request):
	properties = public_properties()
	property_cards = []
	for property_obj in properties:
		room = property_obj.room_types.order_by('base_price').first()
		price_per_night = room.base_price if room else None
		review_count = property_obj.reviews.count()
		property_cards.append({
			'property': property_obj,
			'price_per_night': price_per_night,
			'review_count': review_count,
		})
	return render(request, 'hotels/list.html', {'property_cards': property_cards})


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
	}
	return render(request, 'hotels/detail.html', context)

# Create your views here.
