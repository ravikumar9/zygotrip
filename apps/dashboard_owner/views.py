from django.contrib import messages
from django.shortcuts import redirect, render
from apps.accounts.permissions import role_required, provider_required
from apps.hotels.services import create_property, submit_property_for_approval
from .forms import (
    MealPlanForm, PriceForm, PropertyForm, RoomTypeForm,
    PropertyImageForm, RoomImageForm, PropertyOfferForm, RatingAggregateForm
)
from .selectors import get_owner_properties, get_property_or_404, get_room_or_404, get_or_create_rating
from .services import (
	create_property_image,
	save_property_image,
	save_room,
	save_room_image,
	save_meal,
	save_offer,
	update_rating,
)


@role_required('property_owner')
def dashboard(request):
	properties = get_owner_properties(request.user)
	return render(request, 'dashboard_owner/dashboard.html', {'properties': properties})


@provider_required
def add_property(request):
	form = PropertyForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		property_obj = create_property(request.user, **form.cleaned_data)
		image_url = request.POST.get('image_url', '').strip()
		create_property_image(property_obj, image_url)
		messages.success(request, 'Property created.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_property.html', {'form': form})


@role_required('property_owner')
def add_property_image(request, property_id):
	"""Upload images for a property"""
	property_obj = get_property_or_404(property_id, request.user)
	form = PropertyImageForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		save_property_image(form, property_obj)
		messages.success(request, 'Image uploaded successfully.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_property_image.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def add_room(request, property_id):
	property_obj = get_property_or_404(property_id, request.user)
	form = RoomTypeForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		save_room(form, property_obj)
		messages.success(request, 'Room added.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_room.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def add_room_image(request, room_id):
	"""Upload images for a room type"""
	room = get_room_or_404(room_id, request.user)
	form = RoomImageForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		save_room_image(form, room)
		messages.success(request, 'Room image uploaded successfully.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_room_image.html', {'form': form, 'room': room})


@role_required('property_owner')
def add_meal(request, property_id):
	property_obj = get_property_or_404(property_id, request.user)
	form = MealPlanForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		save_meal(form, property_obj)
		messages.success(request, 'Meal plan added.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_meal.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def add_offer(request, property_id):
	"""Create promotional offer for a property"""
	property_obj = get_property_or_404(property_id, request.user)
	form = PropertyOfferForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		save_offer(form, property_obj)
		messages.success(request, 'Offer created successfully.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_offer.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def update_ratings(request, property_id):
	"""Update rating breakdown for a property"""
	property_obj = get_property_or_404(property_id, request.user)
	rating_obj, created = get_or_create_rating(property_obj)
	form = RatingAggregateForm(request.POST or None, instance=rating_obj)
	if request.method == 'POST' and form.is_valid():
		update_rating(property_obj, rating_obj, form)
		messages.success(request, 'Rating breakdown updated.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/update_ratings.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def set_price(request, room_id):
	room = get_room_or_404(room_id, request.user)
	form = PriceForm(request.POST or None, instance=room)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Price updated.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/set_price.html', {'form': form, 'room': room})


@role_required('property_owner')
def submit_approval(request, property_id):
	property_obj = get_property_or_404(property_id, request.user)
	submit_property_for_approval(property_obj)
	messages.success(request, 'Property submitted for approval.')
# Create your views here.