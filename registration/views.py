from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from accounts.selectors import user_has_role
from accounts.models import Role, UserRole
from apps.hotels.models import Property
from .forms import PropertyRegistrationForm, BusRegistrationForm, CabRegistrationForm
from core.location_models import City
from buses.models import Bus
from cabs.models import Cab


@login_required
def register_property(request):
	"""Property registration for owners"""
	if not user_has_role(request.user, 'property_owner'):
		# Assign property_owner role if not present
		role, _ = Role.objects.get_or_create(code='property_owner', defaults={'name': 'Property Owner'})
		UserRole.objects.get_or_create(user=request.user, role=role)
	
	if request.method == 'POST':
		form = PropertyRegistrationForm(request.POST)
		if form.is_valid():
			property_obj = form.save(commit=False)
			property_obj.owner = request.user
			property_obj.save()
			messages.success(request, f'Property "{property_obj.name}" registered successfully!')
			return redirect('dashboard_owner:property_list')  # or appropriate dashboard
	else:
		form = PropertyRegistrationForm()
	
	return render(request, 'registration/property_register.html', {'form': form})


@login_required
def register_bus(request):
	"""Bus registration for operators"""
	if not user_has_role(request.user, 'bus_owner'):
		role, _ = Role.objects.get_or_create(code='bus_owner', defaults={'name': 'Bus Owner'})
		UserRole.objects.get_or_create(user=request.user, role=role)
	
	if request.method == 'POST':
		form = BusRegistrationForm(request.POST)
		if form.is_valid():
			# Create Bus object
			bus = Bus.objects.create(
				operator=request.user,
				name=form.cleaned_data['bus_name'],
				registration_number=form.cleaned_data['registration_number'],
				capacity=form.cleaned_data['capacity'],
				route_from=form.cleaned_data['route_from'],
				route_to=form.cleaned_data['route_to'],
				base_fare=form.cleaned_data['base_fare'],
			)
			messages.success(request, f'Bus "{bus.name}" registered successfully!')
			return redirect('buses:dashboard')
	else:
		form = BusRegistrationForm()
	
	return render(request, 'registration/bus_register.html', {'form': form})


@login_required
def register_cab(request):
	"""Cab registration for operators"""
	if not user_has_role(request.user, 'cab_owner'):
		role, _ = Role.objects.get_or_create(code='cab_owner', defaults={'name': 'Cab Owner'})
		UserRole.objects.get_or_create(user=request.user, role=role)
	
	if request.method == 'POST':
		form = CabRegistrationForm(request.POST)
		if form.is_valid():
			# Create Cab object
			cab = Cab.objects.create(
				operator=request.user,
				vehicle_type=form.cleaned_data['vehicle_type'],
				registration_number=form.cleaned_data['registration_number'],
				city_coverage=form.cleaned_data['city_coverage'],
				base_fare=form.cleaned_data['base_fare'],
			)
			messages.success(request, f'Cab registered successfully!')
			return redirect('cabs:dashboard')
	else:
		form = CabRegistrationForm()
	
	return render(request, 'registration/cab_register.html', {'form': form})
