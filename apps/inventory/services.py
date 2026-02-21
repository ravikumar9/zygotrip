"""
Write operations for inventory domain
PHASE 2: Domain standardization
"""
from django.db import transaction
from datetime import timedelta
from apps.rooms.models import RoomInventory


@transaction.atomic
def initialize_inventory(room_type, start_date, end_date, total_rooms):
    """Initialize inventory for room type across date range"""
    current_date = start_date
    created = []
    
    while current_date < end_date:
        inventory, _ = RoomInventory.objects.get_or_create(
            room_type=room_type,
            date=current_date,
            defaults={
                'total': total_rooms,
                'available': total_rooms,
                'booked': 0
            }
        )
        created.append(inventory)
        current_date += timedelta(days=1)
    
    return created


@transaction.atomic
def reserve_inventory(room_type, start_date, end_date, quantity):
    """Reserve inventory for booking (decrease available)"""
    current_date = start_date
    updated = []
    
    while current_date < end_date:
        inventory = RoomInventory.objects.select_for_update().get(
            room_type=room_type,
            date=current_date
        )
        
        if inventory.available < quantity:
            raise ValueError(f"Insufficient inventory on {current_date}")
        
        inventory.available -= quantity
        inventory.booked += quantity
        inventory.save()
        updated.append(inventory)
        current_date += timedelta(days=1)
    
    return updated


@transaction.atomic
def release_inventory(room_type, start_date, end_date, quantity):
    """Release inventory (increase available, decrease booked)"""
    current_date = start_date
    updated = []
    
    while current_date < end_date:
        inventory = RoomInventory.objects.select_for_update().get(
            room_type=room_type,
            date=current_date
        )
        
        inventory.available += quantity
        inventory.booked = max(0, inventory.booked - quantity)
        inventory.save()
        updated.append(inventory)
        current_date += timedelta(days=1)
    
    return updated


@transaction.atomic
def update_inventory_total(room_type, start_date, end_date, new_total):
    """Update total inventory and adjust available"""
    current_date = start_date
    updated = []
    
    while current_date < end_date:
        inventory = RoomInventory.objects.get(
            room_type=room_type,
            date=current_date
        )
        
        # Adjust available proportionally
        diff = new_total - inventory.total
        inventory.total = new_total
        inventory.available = max(0, inventory.available + diff)
        inventory.save()
        updated.append(inventory)
        current_date += timedelta(days=1)
    
    return updated