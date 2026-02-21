from django.db import models
from datetime import date


class RoomType(models.Model):
    """Stub RoomType model for booking forms."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    capacity = models.IntegerField(default=1)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_guests = models.IntegerField(default=1)
    bed_type = models.CharField(max_length=50, blank=True, null=True)
    room_size_sqm = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        app_label = 'rooms'

    def __str__(self):
        return self.name


class RoomInventory(models.Model):
    """Stub RoomInventory model for tracking available rooms."""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    inventory_date = models.DateField(default=date.today)
    available_count = models.IntegerField(default=0)
    booked_count = models.IntegerField(default=0)

    class Meta:
        app_label = 'rooms'
        unique_together = ['room_type', 'inventory_date']

    def __str__(self):
        return f"{self.room_type.name} - {self.inventory_date}"


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