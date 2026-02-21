from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from apps.core.services import user_has_role, get_dashboard_data, get_home_data


def home(request):
	properties, categories = get_home_data(limit=6)
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

	context = get_dashboard_data(request.user)
	return render(request, 'dashboard/dashboard.html', context)

# Create your views here.