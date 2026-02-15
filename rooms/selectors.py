from .models import RoomInventory


def inventory_for_range(room_type, start_date, end_date):
    return RoomInventory.objects.filter(room_type=room_type, date__gte=start_date, date__lt=end_date)
