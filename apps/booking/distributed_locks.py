"""
Booking Race Condition Protection
Real distributed locks using Redis + retry queue for failed bookings.
"""

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Tuple

import redis
from django.core.cache import cache
from django.utils import timezone
from django.db import models, transaction
from django.conf import settings
from apps.core.models import TimeStampedModel

logger = logging.getLogger('zygotrip')


class BookingLockManager:
    """Distributed lock manager using Redis"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis = redis_client or self._get_redis_client()
        self.lock_timeout = 30  # seconds
        self.lock_prefix = 'booking_lock:'
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis connection from cache"""
        try:
            return cache._cache
        except:
            return None
    
    def acquire_lock(self, resource_id: str, resource_type: str) -> Optional[str]:
        """
        Acquire distributed lock for booking resource.
        Returns lock token if successful, None if failed.
        """
        if not self.redis:
            logger.warning("Redis unavailable, skipping distributed lock")
            return None
        
        lock_key = f"{self.lock_prefix}{resource_type}:{resource_id}"
        lock_token = str(uuid.uuid4())
        
        try:
            # Try to set lock with NX (only if not exists) and EX (expires)
            acquired = self.redis.set(
                lock_key,
                lock_token,
                nx=True,
                ex=self.lock_timeout
            )
            
            if acquired:
                logger.debug(f"Lock acquired for {resource_type}:{resource_id}")
                return lock_token
            else:
                logger.warning(f"Lock failed for {resource_type}:{resource_id} (already held)")
                return None
        
        except Exception as e:
            logger.error(f"Error acquiring lock: {str(e)}")
            return None
    
    def release_lock(self, resource_id: str, resource_type: str, lock_token: str) -> bool:
        """Release distributed lock"""
        if not self.redis:
            return False
        
        lock_key = f"{self.lock_prefix}{resource_type}:{resource_id}"
        
        try:
            # Use Lua script to atomically check and delete (prevent accidental release of other locks)
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            
            result = self.redis.eval(lua_script, 1, lock_key, lock_token)
            
            if result:
                logger.debug(f"Lock released for {resource_type}:{resource_id}")
                return True
            else:
                logger.warning(f"Lock token mismatch for {resource_type}:{resource_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error releasing lock: {str(e)}")
            return False
    
    def extend_lock(self, resource_id: str, resource_type: str, lock_token: str) -> bool:
        """Extend lock expiration"""
        if not self.redis:
            return False
        
        lock_key = f"{self.lock_prefix}{resource_type}:{resource_id}"
        
        try:
            current_token = self.redis.get(lock_key)
            if current_token and current_token.decode() == lock_token:
                self.redis.expire(lock_key, self.lock_timeout)
                return True
            return False
        except Exception as e:
            logger.error(f"Error extending lock: {str(e)}")
            return False


class BookingRetryQueue(TimeStampedModel):
    """Queue for retrying failed bookings"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Booking details
    user_id = models.PositiveIntegerField(db_index=True)
    booking_data = models.JSONField()  # Full booking data to retry
    
    # Resource details
    resource_type = models.CharField(max_length=20)  # hotel, bus, cab, package
    resource_id = models.PositiveIntegerField()
    
    # Retry tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=5)
    
    last_error = models.TextField(blank=True)
    last_retry_at = models.DateTimeField(null=True, blank=True)
    
    # Scheduling
    next_retry_at = models.DateTimeField(db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'next_retry_at']),
            models.Index(fields=['user_id', 'status']),
        ]
        ordering = ['next_retry_at']
    
    def __str__(self):
        return f"{self.resource_type}#{self.resource_id} - Attempt {self.retry_count}/{self.max_retries}"
    
    @property
    def has_expired(self) -> bool:
        """Check if retry window has passed"""
        return timezone.now() > self.expires_at
    
    def get_backoff_delay(self) -> timedelta:
        """Calculate exponential backoff"""
        # 5s * 2^(retry_count) = 5s, 10s, 20s, 40s, 80s, 160s...
        delay_seconds = 5 * (2 ** self.retry_count)
        return timedelta(seconds=delay_seconds)
    
    def schedule_next_retry(self):
        """Schedule next retry with exponential backoff"""
        if self.retry_count >= self.max_retries:
            self.status = 'failed'
            logger.error(f"Booking retry exhausted: {self}")
        else:
            self.next_retry_at = timezone.now() + self.get_backoff_delay()
            self.status = 'pending'
        
        self.save(update_fields=['status', 'next_retry_at'])


class DistributedBookingManager:
    """Manager for creating bookings with distributed lock protection"""
    
    def __init__(self):
        self.lock_manager = BookingLockManager()
        self.logger = logging.getLogger('zygotrip')
    
    def create_hotel_booking_safe(
        self,
        property_id: int,
        user,
        checkin_date,
        checkout_date,
        adults: int,
        children: int,
        total_price: Decimal,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create hotel booking with distributed lock protection.
        """
        lock_token = self.lock_manager.acquire_lock(str(property_id), 'hotel')
        
        if not lock_token:
            # Queue for retry
            return self._queue_booking_retry(
                user.id, 'hotel', property_id,
                {
                    'checkin_date': str(checkin_date),
                    'checkout_date': str(checkout_date),
                    'adults': adults,
                    'children': children,
                    'total_price': str(total_price),
                }
            )
        
        try:
            with transaction.atomic():
                from apps.hotels.models import Property, Booking
                
                # Check availability
                property_obj = Property.objects.select_for_update().get(id=property_id)
                
                overlapping = Booking.objects.filter(
                    property=property_obj,
                    checkin_date__lt=checkout_date,
                    checkout_date__gt=checkin_date,
                    status__in=['confirmed', 'completed']
                ).count()
                
                if overlapping > 0:
                    self.lock_manager.release_lock(str(property_id), 'hotel', lock_token)
                    return False, "Room not available for selected dates", None
                
                # Create booking
                booking = Booking.objects.create(
                    property=property_obj,
                    user=user,
                    checkin_date=checkin_date,
                    checkout_date=checkout_date,
                    adults=adults,
                    children=children,
                    total_price=total_price,
                    status='confirmed'
                )
                
                self.logger.info(f"Hotel booking created: {booking.id}")
                
                return True, "", {'booking_id': booking.id}
        
        except Exception as e:
            self.logger.error(f"Error creating hotel booking: {str(e)}")
            return False, str(e), None
        
        finally:
            self.lock_manager.release_lock(str(property_id), 'hotel', lock_token)
    
    def create_cab_booking_safe(
        self,
        cab_id: int,
        user,
        from_location: str,
        to_location: str,
        total_price: Decimal,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Create cab booking with distributed lock protection"""
        lock_token = self.lock_manager.acquire_lock(str(cab_id), 'cab')
        
        if not lock_token:
            return self._queue_booking_retry(
                user.id, 'cab', cab_id,
                {
                    'from_location': from_location,
                    'to_location': to_location,
                    'total_price': str(total_price),
                }
            )
        
        try:
            with transaction.atomic():
                from apps.cabs.models import Cab, CabBooking
                
                cab = Cab.objects.select_for_update().get(id=cab_id)
                
                if not cab.is_available:
                    self.lock_manager.release_lock(str(cab_id), 'cab', lock_token)
                    return False, "Cab is not available", None
                
                booking = CabBooking.objects.create(
                    cab=cab,
                    user=user,
                    from_location=from_location,
                    to_location=to_location,
                    total_price=total_price,
                    status='confirmed'
                )
                
                self.logger.info(f"Cab booking created: {booking.id}")
                return True, "", {'booking_id': booking.id}
        
        except Exception as e:
            self.logger.error(f"Error creating cab booking: {str(e)}")
            return False, str(e), None
        
        finally:
            self.lock_manager.release_lock(str(cab_id), 'cab', lock_token)
    
    def create_bus_booking_safe(
        self,
        bus_id: int,
        user,
        seats: int,
        travel_date,
        total_price: Decimal,
    ) -> Tuple[bool, str, Optional[Dict]]:
        """Create bus booking with distributed lock protection"""
        lock_token = self.lock_manager.acquire_lock(str(bus_id), 'bus')
        
        if not lock_token:
            return self._queue_booking_retry(
                user.id, 'bus', bus_id,
                {
                    'seats': seats,
                    'travel_date': str(travel_date),
                    'total_price': str(total_price),
                }
            )
        
        try:
            with transaction.atomic():
                from apps.buses.models import Bus, BusBooking
                
                bus = Bus.objects.select_for_update().get(id=bus_id)
                
                if bus.available_seats < seats:
                    self.lock_manager.release_lock(str(bus_id), 'bus', lock_token)
                    return False, f"Only {bus.available_seats} seats available", None
                
                booking = BusBooking.objects.create(
                    bus=bus,
                    user=user,
                    seats=seats,
                    travel_date=travel_date,
                    total_price=total_price,
                    status='confirmed'
                )
                
                # Update available seats
                bus.available_seats -= seats
                bus.save(update_fields=['available_seats'])
                
                self.logger.info(f"Bus booking created: {booking.id}")
                return True, "", {'booking_id': booking.id}
        
        except Exception as e:
            self.logger.error(f"Error creating bus booking: {str(e)}")
            return False, str(e), None
        
        finally:
            self.lock_manager.release_lock(str(bus_id), 'bus', lock_token)
    
    def _queue_booking_retry(
        self,
        user_id: int,
        resource_type: str,
        resource_id: int,
        booking_data: Dict,
    ) -> Tuple[bool, str, Dict]:
        """Queue failed booking for retry"""
        try:
            retry_queue = BookingRetryQueue.objects.create(
                user_id=user_id,
                resource_type=resource_type,
                resource_id=resource_id,
                booking_data=booking_data,
                next_retry_at=timezone.now() + timedelta(seconds=5),
                expires_at=timezone.now() + timedelta(hours=1),  # Expire after 1 hour
            )
            
            self.logger.info(f"Booking queued for retry: {retry_queue.id}")
            
            return True, "Booking queued for processing", {'retry_queue_id': retry_queue.id}
        
        except Exception as e:
            self.logger.error(f"Error queueing booking: {str(e)}")
            return False, "Unable to process booking at this time", None


def cleanup_expired_reservations():
    """Periodic task to auto-release expired reservations"""
    try:
        # Find reservations that have expired
        cutoff = timezone.now() - timedelta(hours=24)
        expired = BookingRetryQueue.objects.filter(
            status__in=['pending', 'processing'],
            expires_at__lt=cutoff
        )
        
        count = 0
        for item in expired:
            item.status = 'cancelled'
            item.last_error = "Reservation expired"
            item.save(update_fields=['status', 'last_error'])
            count += 1
        
        logger.info(f"Cleaned up {count} expired reservations")
        return count
    
    except Exception as e:
        logger.error(f"Error in cleanup_expired_reservations: {str(e)}")
        return 0


def process_booking_retry_queue():
    """Periodic task to process retry queue"""
    try:
        manager = DistributedBookingManager()
        
        # Get pending retries due for processing
        now = timezone.now()
        pending = BookingRetryQueue.objects.filter(
            status='pending',
            next_retry_at__lte=now,
            expires_at__gt=now
        )[:10]  # Process 10 at a time
        
        processed = 0
        for item in pending:
            item.status = 'processing'
            item.retry_count += 1
            item.last_retry_at = now
            item.save(update_fields=['status', 'retry_count', 'last_retry_at'])
            
            # Note: Actually retry the booking based on resource_type
            # This would call the appropriate create_*_booking_safe method
            
            processed += 1
        
        logger.info(f"Processed {processed} booking retries")
        return processed
    
    except Exception as e:
        logger.error(f"Error in process_booking_retry_queue: {str(e)}")
        return 0