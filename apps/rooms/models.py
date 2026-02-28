"""Room models with production-grade inventory management."""
from django.db import models, models as dj_models
from django.core.validators import MinValueValidator
from datetime import date


class RoomType(models.Model):
    """Stub RoomType model for booking forms."""
    property = models.ForeignKey('hotels.Property', on_delete=models.CASCADE, related_name='room_types', null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    capacity = models.IntegerField(default=1)
    max_occupancy = models.IntegerField(default=1)
    room_size = models.IntegerField(default=250, help_text="Room size in sq ft")
    available_count = models.IntegerField(default=10, help_text="Available rooms of this type")
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_guests = models.IntegerField(default=1)
    bed_type = models.CharField(max_length=50, blank=True, null=True)
    room_size_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    meal_plan = models.CharField(
        max_length=50,
        choices=[
            ('room_only', 'Room Only'),
            ('breakfast', 'Room + Breakfast'),
            ('half_board', 'Room + Breakfast + Dinner'),
            ('full_board', 'Room + All Meals'),
            ('all_inclusive', 'All Inclusive'),
        ],
        default='room_only',
        help_text='Meal plan included with room'
    )

    class Meta:
        app_label = 'rooms'

    def __str__(self):
        return self.name


class RoomInventory(models.Model):
    """
    Production-grade room inventory with date-wise tracking.
    
    PHASE 5, PROMPTS 8-9: Inventory Hardening
    
    HARDENED RULES:
    1. One entry per (room_type, date) - enforced by unique_together
    2. DB-level constraint: available_rooms >= 0
    3. Optimized query paths via indexes
    4. Temple towns: indexed by (hotel, date) for spike days
    5. Prevent negative inventory at DB level
    """
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.CASCADE,
        related_name='inventories'
    )
    
    date = models.DateField(
        default=date.today,
        db_index=True,
        help_text="Inventory date"
    )
    
    # Inventory state (date-specific)
    available_rooms = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],  # Python validation
        help_text="Rooms available for booking"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Price per room per night for this date"
    )
    
    is_closed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Is date closed for bookings (e.g., maintenance)"
    )
    
    # Legacy fields (for compatibility)
    available_count = models.IntegerField(default=0)
    booked_count = models.IntegerField(default=0)
    inventory_date = models.DateField(auto_now_add=True)

    class Meta:
        app_label = 'rooms'
        unique_together = [('room_type', 'date')]  # One per date
        indexes = [
            dj_models.Index(fields=['room_type', 'date']),
            dj_models.Index(fields=['room_type', 'date', 'is_closed']),
            # For temple town queries (spike days)
            dj_models.Index(fields=['date', 'is_closed']),
        ]
        # DB-level constraint: no negative inventory
        constraints = [
            dj_models.CheckConstraint(
                check=dj_models.Q(available_rooms__gte=0),
                name='%(class)s_available_rooms_non_negative'
            ),
        ]

    def __str__(self):
        return f"{self.room_type.name} - {self.date} ({self.available_rooms} available)"


class RoomImage(models.Model):
    """Stub RoomImage model for room images."""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)

    class Meta:
        app_label = 'rooms'

    def __str__(self):
        return f"Image for {self.room_type.name}"


class RoomAmenity(models.Model):
    """Room-specific amenities (separate from property amenities)
    
    Examples:
    - Premium Suite: jacuzzi, balcony, premium bedding
    - Standard Room: wifi, TV, AC
    
    Allows showing room-specific features instead of property-wide features
    """
    room_type = models.ForeignKey(
        RoomType, on_delete=models.CASCADE, related_name='amenities'
    )
    name = models.CharField(max_length=120)
    icon = models.CharField(max_length=40, blank=True)
    
    class Meta:
        app_label = 'rooms'
        verbose_name_plural = 'Room Amenities'
        unique_together = ('room_type', 'name')
    
    def __str__(self):
        return f"{self.room_type.name} - {self.name}"
