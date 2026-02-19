from decimal import Decimal
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.permissions import provider_required
from .models import Bus, BusSeat, BusBooking, BusBookingPassenger, BusPriceBreakdown, BusType
from .serializers import BusRenderReadySerializer
from .forms import BusRegistrationForm, BusSeatBookingForm

def list_buses(request):
    from django.core.paginator import Paginator
    
    buses = Bus.objects.filter(is_active=True)
    from_city = request.GET.get('from_city', '').strip()
    to_city = request.GET.get('to_city', '').strip()
    journey_date = request.GET.get('date', '').strip()
    search_query = request.GET.get('q', '').strip()

    # Search - Bus model doesn't have 'name' field, search by operator_name or from/to city
    if search_query:
        buses = buses.filter(
            Q(operator_name__icontains=search_query) |
            Q(from_city__icontains=search_query) |
            Q(to_city__icontains=search_query)
        )
    
    # Filters
    if from_city:
        buses = buses.filter(from_city__icontains=from_city)
    if to_city:
        buses = buses.filter(to_city__icontains=to_city)
    if journey_date:
        buses = buses.filter(journey_date=journey_date)

    # Sorting - Bus model doesn't have rating field
    sort_by = request.GET.get('sort', '').strip()
    if sort_by == 'price_low':
        buses = buses.order_by('price_per_seat')
    elif sort_by == 'price_high':
        buses = buses.order_by('-price_per_seat')
    elif sort_by == 'departure':
        buses = buses.order_by('departure_time')
    else:
        # Default sort by departure time
        buses = buses.order_by('departure_time')

    # Pagination
    paginator = Paginator(buses, 20)
    page = request.GET.get('page', '1')
    try:
        page_num = int(page)
        if page_num < 1:
            page_num = 1
        page_obj = paginator.get_page(page_num)
    except (ValueError, TypeError):
        page_obj = paginator.get_page(1)

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
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)
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


def _ensure_bus_seats(bus):
    if bus.seats.exists():
        return
    total_seats = bus.available_seats or (bus.bus_type.capacity if bus.bus_type_id else 40)
    seats_to_create = []
    seat_index = 0
    for i in range(total_seats):
        row = chr(ord('A') + (seat_index // 4))
        column = (seat_index % 4) + 1
        seat_number = f"{row}{column}"
        seats_to_create.append(
            BusSeat(
                bus=bus,
                seat_number=seat_number,
                row=row,
                column=column,
                is_ladies_seat=False,
                state=BusSeat.AVAILABLE,
            )
        )
        seat_index += 1
    BusSeat.objects.bulk_create(seats_to_create)


@login_required
def bus_booking(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id, is_active=True)
    _ensure_bus_seats(bus)
    available_seats = bus.seats.filter(state=BusSeat.AVAILABLE).order_by('row', 'column')
    seat_choices = [(str(seat.id), seat.seat_number) for seat in available_seats]

    if request.method == 'POST':
        form = BusSeatBookingForm(request.POST, seat_choices=seat_choices)
        if form.is_valid():
            seat_id = int(form.cleaned_data['seat_id'])
            journey_date = form.cleaned_data['journey_date']
            promo_code = form.cleaned_data['promo_code'].strip()

            with transaction.atomic():
                seat = BusSeat.objects.select_for_update().get(id=seat_id, bus=bus)
                if seat.state != BusSeat.AVAILABLE:
                    messages.error(request, 'Selected seat is no longer available.')
                    return redirect('buses:booking', bus_id=bus.id)

                base_amount = Decimal(bus.price_per_seat)
                service_fee = Decimal('50')
                gst = (base_amount * Decimal('0.05')).quantize(Decimal('1.00'))
                total_amount = base_amount + service_fee + gst

                booking = BusBooking.objects.create(
                    user=request.user,
                    bus=bus,
                    journey_date=journey_date,
                    status=BusBooking.STATUS_CONFIRMED,
                    total_amount=total_amount,
                    promo_code=promo_code,
                )
                BusBookingPassenger.objects.create(
                    booking=booking,
                    seat=seat,
                    full_name=form.cleaned_data['passenger_full_name'],
                    age=form.cleaned_data['passenger_age'],
                    gender=form.cleaned_data['passenger_gender'],
                    phone=form.cleaned_data['passenger_phone'],
                )
                BusPriceBreakdown.objects.create(
                    booking=booking,
                    base_amount=base_amount,
                    service_fee=service_fee,
                    gst=gst,
                    promo_discount=Decimal('0'),
                    total_amount=total_amount,
                )

                seat.state = BusSeat.BOOKED
                seat.save(update_fields=['state', 'updated_at'])
                if bus.available_seats > 0:
                    bus.available_seats -= 1
                    bus.save(update_fields=['available_seats', 'updated_at'])

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
    booking = get_object_or_404(BusBooking, uuid=booking_uuid, user=request.user)
    context = {'booking': booking}
    return render(request, 'buses/booking_success.html', context)

@login_required
def booking_review(request, booking_uuid):
    booking = get_object_or_404(BusBooking, uuid=booking_uuid, user=request.user)
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
            
            # Ensure bus_type exists - get or create default
            if not bus.bus_type_id:
                default_type, _ = BusType.objects.get_or_create(
                    name=BusType.SEATER,
                    defaults={'base_fare': 500, 'capacity': 40}
                )
                bus.bus_type = default_type
            
            bus.save()
            messages.success(request, 'Bus registered successfully!')
            return redirect('buses:list')
    else:
        form = BusRegistrationForm()
    
    context = {'form': form}
    return render(request, 'buses/owner_registration.html', context)

