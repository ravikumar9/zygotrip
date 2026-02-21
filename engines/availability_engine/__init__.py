"""
Availability Engine - Room/inventory availability logic
PHASE 3: Extracted from inventory/booking apps
CRITICAL RULE: NO app imports - uses pure Python logic
"""
from datetime import date, timedelta
from typing import List, Dict, Any


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """Generate list of dates between start and end (exclusive)"""
    dates = []
    current = start_date
    while current < end_date:
        dates.append(current)
        current += timedelta(days=1)
    return dates


def check_availability_sufficient(
    inventory_data: List[Dict[str, Any]],
    required_quantity: int
) -> bool:
    """
    Check if inventory is sufficient for required quantity
    
    Args:
        inventory_data: List of dicts with 'date' and 'available' keys
        required_quantity: Number of units required
    
    Returns:
        True if all dates have sufficient availability
    """
    for inv in inventory_data:
        if inv.get('available', 0) < required_quantity:
            return False
    return True


def find_first_unavailable_date(
    inventory_data: List[Dict[str, Any]],
    required_quantity: int
) -> date | None:
    """
    Find first date with insufficient availability
    
    Args:
        inventory_data: List of dicts with 'date' and 'available'
        required_quantity: Number of units required
    
    Returns:
        First unavailable date or None if all available
    """
    for inv in inventory_data:
        if inv.get('available', 0) < required_quantity:
            return inv.get('date')
    return None


def calculate_total_capacity(inventory_data: List[Dict[str, Any]]) -> int:
    """Calculate total capacity across date range"""
    return sum(inv.get('total', 0) for inv in inventory_data)


def calculate_utilization_percentage(
    total: int,
    available: int
) -> float:
    """Calculate inventory utilization percentage"""
    if total == 0:
        return 0.0
    booked = total - available
    return round((booked / total) * 100, 2)


def get_availability_status(
    available: int,
    total: int
) -> str:
    """
    Get availability status label
    
    Returns:
        'sold_out', 'low', 'moderate', or 'high'
    """
    if available == 0:
        return 'sold_out'
    
    utilization = calculate_utilization_percentage(total, available)
    
    if utilization >= 90:
        return 'low'  # Low availability (90%+ sold)
    elif utilization >= 50:
        return 'moderate'
    else:
        return 'high'


def calculate_overbooking_threshold(total_inventory: int, overbooking_rate: float = 0.10) -> int:
    """
    Calculate safe overbooking threshold
    
    Args:
        total_inventory: Total inventory count
        overbooking_rate: Overbooking percentage (default 10%)
    
    Returns:
        Maximum bookable units including overbooking buffer
    """
    return int(total_inventory * (1 + overbooking_rate))


def is_blackout_date(check_date: date, blackout_dates: List[date]) -> bool:
    """Check if date is in blackout period"""
    return check_date in blackout_dates


def filter_available_dates(
    start_date: date,
    end_date: date,
    blackout_dates: List[date]
) -> List[date]:
    """Filter out blackout dates from range"""
    all_dates = generate_date_range(start_date, end_date)
    return [d for d in all_dates if not is_blackout_date(d, blackout_dates)]