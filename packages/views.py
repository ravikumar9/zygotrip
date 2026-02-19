from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.permissions import provider_required
from .models import Package, PackageBooking, PackageCategory, PackagePriceBreakdown, PackageTraveler
from .forms import PackageRegistrationForm, PackageBookingCreateForm

def list_packages(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    packages = Package.objects.filter(is_active=True)
    
    # Get filters from request
    category = (request.GET.get('category') or '').strip()
    duration = (request.GET.get('duration') or '').strip()
    price_max = (request.GET.get('price_max') or '').strip()
    search_query = (request.GET.get('q') or '').strip()
    
    # Search
    if search_query:
        packages = packages.filter(
            Q(name__icontains=search_query) |
            Q(destination__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Apply filters
    if category:
        packages = packages.filter(category__name=category)
    if duration:
        if duration.isdigit():
            packages = packages.filter(duration_days=int(duration))
    if price_max:
        try:
            packages = packages.filter(base_price__lte=Decimal(price_max))
        except (InvalidOperation, ValueError):
            pass
    
    # Sorting
    sort_by = (request.GET.get('sort') or '').strip()
    if sort_by == 'price_low':
        packages = packages.order_by('base_price')
    elif sort_by == 'price_high':
        packages = packages.order_by('-base_price')
    elif sort_by == 'duration':
        packages = packages.order_by('duration_days')
    elif sort_by == 'rating':
        packages = packages.order_by('-rating')
    else:
        packages = packages.order_by('-rating', 'base_price')
    
    # Pagination
    paginator = Paginator(packages, 20)
    page = request.GET.get('page', '1')
    try:
        page_num = int(page)
        if page_num < 1:
            page_num = 1
        page_obj = paginator.get_page(page_num)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)
    
    # Create cards (serialized format for template rendering)
    cards = [
        {
            'id': pkg.id,
            'name': pkg.name,
            'description': pkg.description,
            'price_current': float(pkg.base_price),
            'image_url': pkg.image_url,
            'rating_value': float(pkg.rating) if pkg.rating else 0,
            'duration_days': pkg.duration_days,
            'destination': pkg.destination,
            'cta_url': f'/packages/{pkg.id}/',
            'cta_label': 'View Package',
        }
        for pkg in page_obj.object_list
    ]
    
    context = {
        'cards': cards,
        'category': category or '',
        'duration': duration or '',
        'price_max': price_max or '',
        'search_query': search_query or '',
        'filter_labels': ['Duration', 'Price Range', 'Destination'],
        'filters': {
            'category': category,
            'duration': duration,
            'price_max': price_max,
            'search_query': search_query,
            'sort_by': sort_by,
        },
        'pagination': {
            'page_obj': page_obj,
            'page': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        },
        'meta': {
            'total_results': paginator.count,
        },
        'page_title': 'Holiday Packages - Zygotrip',
        'empty_state': len(cards) == 0,
    }
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
def package_booking(request, package_id):
    package = get_object_or_404(Package, id=package_id, is_active=True)

    if request.method == 'POST':
        form = PackageBookingCreateForm(request.POST)
        if form.is_valid():
            number_of_travelers = form.cleaned_data['number_of_travellers']

            with transaction.atomic():
                package = Package.objects.select_for_update().get(id=package.id)
                if number_of_travelers > package.max_group_size:
                    messages.error(request, 'Not enough availability for this package.')
                    return redirect('packages:booking', package_id=package.id)

                total_amount = Decimal(package.base_price) * Decimal(number_of_travelers)
                booking = PackageBooking.objects.create(
                    user=request.user,
                    package=package,
                    start_date=form.cleaned_data['start_date'],
                    end_date=form.cleaned_data['end_date'],
                    number_of_travelers=number_of_travelers,
                    status=PackageBooking.STATUS_CONFIRMED,
                    total_amount=total_amount,
                    promo_code=form.cleaned_data.get('promo_code', '').strip(),
                )
                PackageTraveler.objects.create(
                    booking=booking,
                    full_name=form.cleaned_data['traveler_full_name'],
                    age=form.cleaned_data['traveler_age'],
                    relationship=form.cleaned_data['traveler_relationship'],
                    email=form.cleaned_data['traveler_email'],
                    phone=form.cleaned_data['traveler_phone'],
                )
                for index in range(2, number_of_travelers + 1):
                    PackageTraveler.objects.create(
                        booking=booking,
                        full_name=f"Traveler {index}",
                        age=form.cleaned_data['traveler_age'],
                        relationship='Companion',
                    )
                PackagePriceBreakdown.objects.create(
                    booking=booking,
                    per_person_base=package.base_price,
                    total_base=total_amount,
                    accommodation=Decimal('0'),
                    meals=Decimal('0'),
                    activities=Decimal('0'),
                    transport=Decimal('0'),
                    service_fee=Decimal('0'),
                    gst=Decimal('0'),
                    promo_discount=Decimal('0'),
                    total_amount=total_amount,
                )
                package.max_group_size -= number_of_travelers
                package.save(update_fields=['max_group_size', 'updated_at'])

            messages.success(request, 'Package booking confirmed!')
            return redirect('packages:booking-success', booking_uuid=booking.uuid)
    else:
        form = PackageBookingCreateForm()

    context = {
        'package': package,
        'form': form,
    }
    return render(request, 'packages/booking.html', context)

@login_required
def booking_review(request, booking_uuid):
    booking = get_object_or_404(PackageBooking, uuid=booking_uuid, user=request.user)
    context = {'booking': booking}
    return render(request, 'packages/review.html', context)


@login_required
def booking_success(request, booking_uuid):
    booking = get_object_or_404(PackageBooking, uuid=booking_uuid, user=request.user)
    context = {'booking': booking}
    return render(request, 'packages/booking_success.html', context)


@provider_required
def owner_package_add(request):
    """
    Package provider registration form for adding new packages
    """
    if request.method == 'POST':
        form = PackageRegistrationForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.provider = request.user
            
            # Ensure category exists - get or create default
            if not package.category_id:
                default_category, _ = PackageCategory.objects.get_or_create(
                    name='General',
                    defaults={'description': 'General travel packages', 'icon': '🌍'}
                )
                package.category = default_category
            
            package.save()
            messages.success(request, 'Package registered successfully!')
            return redirect('packages:list')
    else:
        form = PackageRegistrationForm()
    
    context = {'form': form}
    return render(request, 'packages/owner_registration.html', context)

