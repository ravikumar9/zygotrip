from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Package, PackageBooking

def list_packages(request):
    packages = Package.objects.filter(is_active=True)
    
    # Get filters from request
    category = request.GET.get('category')
    duration = request.GET.get('duration')
    price_max = request.GET.get('price_max')
    
    # Apply filters
    if category:
        packages = packages.filter(category__name=category)
    if duration:
        packages = packages.filter(duration_days=duration)
    if price_max:
        packages = packages.filter(base_price__lte=price_max)
    
    context = {'packages': packages}
    return render(request, 'packages/list.html', context)

def package_detail(request, package_id):
    package = get_object_or_404(Package, id=package_id, is_active=True)
    context = {
        'package': package,
        'itinerary': package.itinerary.all(),
        'inclusions': package.get_inclusions_list(),
        'exclusions': package.get_exclusions_list()
    }
    return render(request, 'packages/detail.html', context)

@login_required
def booking_review(request, booking_uuid):
    booking = get_object_or_404(PackageBooking, uuid=booking_uuid, user=request.user)
    context = {'booking': booking}
    return render(request, 'packages/review.html', context)
