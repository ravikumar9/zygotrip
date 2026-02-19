from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from accounts.permissions import role_required, provider_required
from dashboard_admin.models import PropertyApproval
from hotels.models import Property, PropertyImage, PropertyOffer, RatingAggregate
from hotels.services import create_property, submit_property_for_approval
from meals.models import MealPlan
from rooms.models import RoomType, RoomImage
from .forms import (
    MealPlanForm, PriceForm, PropertyForm, RoomTypeForm,
    PropertyImageForm, RoomImageForm, PropertyOfferForm, RatingAggregateForm
)


@role_required('property_owner')
def dashboard(request):
	properties = Property.objects.filter(owner=request.user, is_active=True).prefetch_related('room_types', 'images', 'offers')
	return render(request, 'dashboard_owner/dashboard.html', {'properties': properties})


@provider_required
def add_property(request):
	form = PropertyForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		property_obj = create_property(request.user, **form.cleaned_data)
		image_url = request.POST.get('image_url', '').strip()
		if image_url:
			try:
				PropertyImage.objects.create(property=property_obj, image_url=image_url, is_featured=True)
			except ValidationError:
				pass
		messages.success(request, 'Property created.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_property.html', {'form': form})


@role_required('property_owner')
def add_property_image(request, property_id):
	"""Upload images for a property"""
	property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
	form = PropertyImageForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		img = form.save(commit=False)
		img.property = property_obj
		img.save()
		messages.success(request, 'Image uploaded successfully.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_property_image.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def add_room(request, property_id):
	property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
	form = RoomTypeForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		room = form.save(commit=False)
		room.property = property_obj
		room.save()
		messages.success(request, 'Room added.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_room.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def add_room_image(request, room_id):
	"""Upload images for a room type"""
	room = get_object_or_404(RoomType, id=room_id, property__owner=request.user)
	form = RoomImageForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		img = form.save(commit=False)
		img.room_type = room
		img.save()
		messages.success(request, 'Room image uploaded successfully.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_room_image.html', {'form': form, 'room': room})


@role_required('property_owner')
def add_meal(request, property_id):
	property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
	form = MealPlanForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		meal = form.save(commit=False)
		meal.property = property_obj
		meal.save()
		messages.success(request, 'Meal plan added.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_meal.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def add_offer(request, property_id):
	"""Create promotional offer for a property"""
	property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
	form = PropertyOfferForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		offer = form.save(commit=False)
		offer.property = property_obj
		offer.save()
		messages.success(request, 'Offer created successfully.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_offer.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def update_ratings(request, property_id):
	"""Update rating breakdown for a property"""
	property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
	rating_obj, created = RatingAggregate.objects.get_or_create(property=property_obj)
	form = RatingAggregateForm(request.POST or None, instance=rating_obj)
	if request.method == 'POST' and form.is_valid():
		form.save()
		# Recalculate overall rating
		avg = (rating_obj.cleanliness + rating_obj.service + rating_obj.location + rating_obj.amenities + rating_obj.value_for_money) / 5
		property_obj.rating = avg
		property_obj.save()
		messages.success(request, 'Rating breakdown updated.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/update_ratings.html', {'form': form, 'property': property_obj})


@role_required('property_owner')
def set_price(request, room_id):
	room = get_object_or_404(RoomType, id=room_id, property__owner=request.user)
	form = PriceForm(request.POST or None, instance=room)
	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Price updated.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/set_price.html', {'form': form, 'room': room})


@role_required('property_owner')
def submit_approval(request, property_id):
	property_obj = get_object_or_404(Property, id=property_id, owner=request.user)
	submit_property_for_approval(property_obj)
	messages.success(request, 'Property submitted for approval.')
# Create your views here.
