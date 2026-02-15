from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.permissions import role_required
from dashboard_admin.models import PropertyApproval
from hotels.models import Property
from hotels.services import create_property, submit_property_for_approval
from meals.models import MealPlan
from rooms.models import RoomType
from .forms import MealPlanForm, PriceForm, PropertyForm, RoomTypeForm


@role_required('property_owner')
def dashboard(request):
	properties = Property.objects.filter(owner=request.user, is_active=True).prefetch_related('room_types')
	return render(request, 'dashboard_owner/dashboard.html', {'properties': properties})


@role_required('property_owner')
def add_property(request):
	form = PropertyForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		property_obj = create_property(request.user, **form.cleaned_data)
		messages.success(request, 'Property created.')
		return redirect('dashboard_owner:dashboard')
	return render(request, 'dashboard_owner/add_property.html', {'form': form})


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
	return redirect('dashboard_owner:dashboard')

# Create your views here.
