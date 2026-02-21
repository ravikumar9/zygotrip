from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.permissions import provider_required
from .serializers import BusRenderReadySerializer
from .forms import BusRegistrationForm, BusSeatBookingForm
from .selectors import (
    get_bus_queryset,
    paginate_buses,
    get_bus_or_404,
    get_booking_or_404,
    get_available_seats,
)
from .services import ensure_bus_seats, create_bus_booking, ensure_default_bus_type

def list_buses(request):
    from_city = request.GET.get('from_city', '').strip()
    to_city = request.GET.get('to_city', '').strip()
    journey_date = request.GET.get('date', '').strip()
    search_query = request.GET.get('q', '').strip()

    sort_by = request.GET.get('sort', '').strip()
    filters = {
        'from_city': from_city,
        'to_city': to_city,
        'journey_date': journey_date,
        'search_query': search_query,
        'sort_by': sort_by,
    }
    buses = get_bus_queryset(filters)
    page = request.GET.get('page', '1')
    page_obj = paginate_buses(buses, page)

    # Apply data contract serialization
    cards = BusRenderReadySerializer.serialize_listing_cards(page_obj.object_list)

    context = {
        'cards': cards,
        'buses': list(page_obj.object_list),
        'from_city': from_city,
        'to_city': to_city,
        'journey_date': journey_date,
        'search_query': search_query,
        'sort_by': sort_by,
        'filter_labels': ['Bus Type', 'Departure Time', 'Operator'],
        'pagination': {
            'page_obj': page_obj,
            'page': page_obj.number,
            'num_pages': page_obj.paginator.num_pages,
            'has_previous': page_obj.has_previous(),
            'has_next': page_obj.has_next(),
            'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
        },
        'filters': {
            'from_city': from_city,
            'to_city': to_city,
            'journey_date': journey_date,
            'search_query': search_query,
            'sort_by': sort_by,
        },
        'page_title': 'Bus Tickets - Zygotrip',
        'empty_state': len(cards) == 0,
    }
    return render(request, 'buses/list.html', context)

def bus_detail(request, bus_id):
    bus = get_bus_or_404(bus_id)
    # Group seats by row for display
    seats_by_row = {}
    for seat in bus.seats.all():
        if seat.row not in seats_by_row:
            seats_by_row[seat.row] = []
        seats_by_row[seat.row].append(seat)
    
    context = {
        'bus': bus,
        'seats_by_row': dict(sorted(seats_by_row.items())),
        'amenities': bus.get_amenities_list()
    }
    return render(request, 'buses/detail.html', context)


@login_required
def bus_booking(request, bus_id):
    bus = get_bus_or_404(bus_id)
    ensure_bus_seats(bus)
    available_seats = get_available_seats(bus)
    seat_choices = [(str(seat.id), seat.seat_number) for seat in available_seats]

    if request.method == 'POST':
        form = BusSeatBookingForm(request.POST, seat_choices=seat_choices)
        if form.is_valid():
            seat_id = int(form.cleaned_data['seat_id'])
            journey_date = form.cleaned_data['journey_date']
            promo_code = form.cleaned_data['promo_code'].strip()

            booking = create_bus_booking(
                request.user,
                bus,
                form,
                seat_id,
                journey_date,
                promo_code,
            )
            if booking is None:
                messages.error(request, 'Selected seat is no longer available.')
                return redirect('buses:booking', bus_id=bus.id)

            messages.success(request, 'Bus booking confirmed!')
            return redirect('buses:booking-success', booking_uuid=booking.uuid)
    else:
        form = BusSeatBookingForm(seat_choices=seat_choices, initial={
            'journey_date': bus.journey_date,
        })

    context = {
        'bus': bus,
        'form': form,
        'available_seats': available_seats,
    }
    return render(request, 'buses/booking.html', context)


@login_required
def booking_success(request, booking_uuid):
    booking = get_booking_or_404(booking_uuid, request.user)
    context = {'booking': booking}
    return render(request, 'buses/booking_success.html', context)

@login_required
def booking_review(request, booking_uuid):
    booking = get_booking_or_404(booking_uuid, request.user)
    context = {'booking': booking}
    return render(request, 'buses/review.html', context)


@provider_required
def owner_bus_add(request):
    """
    Bus operator registration form for adding new buses
    """
    if request.method == 'POST':
        form = BusRegistrationForm(request.POST)
        if form.is_valid():
            bus = form.save(commit=False)
            bus.operator = request.user
            ensure_default_bus_type(bus)
            
            bus.save()
            messages.success(request, 'Bus registered successfully!')
            return redirect('buses:list')
    else:
        form = BusRegistrationForm()
    
    context = {'form': form}
    return render(request, 'buses/owner_registration.html', context)