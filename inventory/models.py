"""
Inventory Management Models - Production Grade

Handles supplier mapping, property synchronization, and inventory tracking
with strict identity validation and concurrency safety.
"""

from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from core.models import TimeStampedModel
from hotels.models import Property


class SupplierPropertyMap(TimeStampedModel):
    """
    Maps internal properties to external supplier properties.
    - One property can map to multiple suppliers
    - Each supplier property maps to exactly one internal property
    - Immutable once verified (prevents accidental remappings)
    """
    
    SUPPLIER_CHOICES = [
        ('booking', 'Booking.com'),
        ('airbnb', 'Airbnb'),
        ('expedia', 'Expedia'),
        ('oyo', 'OYO'),
        ('tripadvisor', 'TripAdvisor'),
    ]
    
    # Relationship (many-to-one: one property has many suppliers)
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='supplier_maps'
    )
    
    # Supplier identification (unique per supplier)
    supplier_name = models.CharField(
        max_length=50,
        choices=SUPPLIER_CHOICES,
        db_index=True
    )
    external_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Supplier's internal ID for this property"
    )
    
    # Supplier property details (for validation)
    supplier_property_name = models.CharField(max_length=255)
    supplier_city = models.CharField(max_length=80)
    supplier_lat = models.FloatField(
        null=True,
        blank=True,
        help_text="Latitude from supplier data"
    )
    supplier_lng = models.FloatField(
        null=True,
        blank=True,
        help_text="Longitude from supplier data"
    )
    
    # Matching confidence
    confidence_score = models.FloatField(
        default=0.0,
        help_text="0.0-1.0 matching confidence score"
    )
    verified = models.BooleanField(
        default=False,
        help_text="Manual verification flag (immutable after True)"
    )

    # Manual override flag
    manual_override = models.BooleanField(
        default=False,
        help_text="True when mapping was manually overridden"
    )
    
    # Audit trail
    verified_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_supplier_maps'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('supplier_name', 'external_id')
        indexes = [
            models.Index(fields=['supplier_name', 'external_id']),
            models.Index(fields=['property', 'verified']),
        ]
        ordering = ['-verified', '-confidence_score']
    
    def __str__(self):
        return f"{self.property.name} → {self.supplier_name} ({self.external_id})"
    
    def clean(self):
        """Validate mapping before save"""
        # Cannot unverify once verified
        if self.pk:
            existing = SupplierPropertyMap.objects.get(pk=self.pk)
            if existing.verified and not self.verified:
                raise ValidationError("Cannot unverify a mapping")
        
        # Confidence must be between 0 and 1
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValidationError("Confidence score must be between 0.0 and 1.0")
        
        # If verified, confidence must be >= 0.8
        if self.verified and self.confidence_score < 0.8:
            raise ValidationError("Verified mappings must have confidence >= 0.8")

        # Manual override requires verified mapping
        if self.manual_override and not self.verified:
            raise ValidationError("Manual override requires verified=True")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class PropertyInventory(TimeStampedModel):
    """
    Tracks real-time inventory per property.
    Used for concurrency-safe deductions.
    """
    
    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    
    # Available rooms
    total_rooms = models.PositiveIntegerField(default=0)
    available_rooms = models.PositiveIntegerField(default=0)
    
    # Sync status
    last_supplier_sync = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('syncing', 'Syncing'),
            ('synced', 'Synced'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    
    # Version for optimistic locking
    version = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = "Property Inventories"
    
    def __str__(self):
        return f"{self.property.name}: {self.available_rooms}/{self.total_rooms}"
    
    def clean(self):
        """Validate inventory constraints"""
        if self.available_rooms > self.total_rooms:
            raise ValidationError("Available rooms cannot exceed total rooms")
        if self.available_rooms < 0 or self.total_rooms < 0:
            raise ValidationError("Room counts cannot be negative")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class PriceHistory(TimeStampedModel):
    """
    Immutable price history log.
    NEVER UPDATE existing rows - only insert new ones.
    Provides complete audit trail for pricing decisions.
    """
    
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    
    # Pricing data (immutable after creation)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Base price before multipliers"
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Final calculated price"
    )
    
    # Pricing factors
    demand_score = models.PositiveSmallIntegerField(
        default=50,
        help_text="0-100 demand indicator"
    )
    competitor_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Competitor reference price"
    )
    
    # Change from previous price
    price_change_percent = models.FloatField(
        default=0.0,
        help_text="% change from previous price"
    )
    
    # Calculated by
    calculated_by = models.CharField(
        max_length=50,
        default='system',
        help_text="Which engine calculated this"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', '-created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name_plural = "Price Histories"
    
    def __str__(self):
        return f"{self.property.name} @ ₹{self.final_price} ({self.created_at.date()})"

    def save(self, *args, **kwargs):
        # Enforce 2-decimal precision by rounding
        if self.base_price is not None:
            self.base_price = Decimal(str(self.base_price)).quantize(Decimal('0.01'))
        if self.final_price is not None:
            self.final_price = Decimal(str(self.final_price)).quantize(Decimal('0.01'))
        if self.competitor_price is not None:
            self.competitor_price = Decimal(str(self.competitor_price)).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)
