from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Bus, BusSeat, BusBooking

def list_buses(request):
    buses = Bus.objects.filter(is_active=True)
    context = {'buses': buses}
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

@login_required
def booking_review(request, booking_uuid):
    booking = get_object_or_404(BusBooking, uuid=booking_uuid, user=request.user)
    context = {'booking': booking}
    return render(request, 'buses/review.html', context)
