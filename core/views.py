from django.shortcuts import render
from hotels.selectors import public_properties


def home(request):
	properties = public_properties()[:6]
	return render(request, 'core/home.html', {'properties': properties})


def permission_denied(request, exception):
	return render(request, '403.html', status=403)

# Create your views here.
