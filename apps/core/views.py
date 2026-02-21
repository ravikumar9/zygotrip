from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.hotels.services import CategoriesService, HotelHighlightService
from apps.accounts.selectors import user_has_role


def home(request):
	properties = HotelHighlightService.featured_properties(limit=6)
	categories = CategoriesService.list_categories()
	return render(request, 'core/home.html', {
		'properties': properties,
		'categories': categories,
	})


def component_library_preview(request):
	"""Component library preview page for design system showcase"""
	return render(request, 'component-library-preview.html')


def permission_denied(request, exception):
	return render(request, '403.html', status=403)


@login_required
def dashboard(request):
	if user_has_role(request.user, 'property_owner'):
		return redirect('dashboard_owner:dashboard')
	if user_has_role(request.user, 'cab_owner'):
		return redirect('cabs:dashboard')
	if user_has_role(request.user, 'bus_operator'):
		return redirect('buses:dashboard')

	from apps.booking.models import Booking
	from apps.hotels.models import Property
	from apps.cabs.models import Cab
	from apps.buses.models import Bus

	bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
	properties = Property.objects.filter(owner=request.user).order_by('-created_at')
	cabs = Cab.objects.filter(owner=request.user).order_by('-created_at')
	buses = Bus.objects.filter(operator=request.user).order_by('-created_at')

	context = {
		'bookings': bookings,
		'properties': properties,
		'cabs': cabs,
		'buses': buses,
	}
	return render(request, 'dashboard/dashboard.html', context)

# Create your views here.