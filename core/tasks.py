import logging
from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Sum
from datetime import timedelta

logger = logging.getLogger('zygotrip')


@shared_task(bind=True, max_retries=3)
def cleanup_expired_bookings(self):
    """
    Cleanup expired/abandoned bookings and refund wallet amounts.
    Runs every 5 minutes via Celery Beat.
    """
    try:
        from apps.booking.models import Booking
        
        # Find bookings that expired before processing
        expired_cutoff = timezone.now() - timedelta(hours=1)
        expired_bookings = Booking.objects.filter(
            status='pending',
            created_at__lt=expired_cutoff,
        )
        
        refunded_count = 0
        for booking in expired_bookings:
            # Refund wallet if applicable
            if booking.user and hasattr(booking, 'refund_booking'):
                try:
                    booking.refund_booking()
                    refunded_count += 1
                except Exception as e:
                    logger.error(f"Failed to refund booking {booking.id}: {str(e)}")
        
        logger.info(
            f"Cleanup expired bookings: {expired_bookings.count()} bookings, "
            f"{refunded_count} refunded",
        )
        return {
            'total_bookings': expired_bookings.count(),
            'refunded': refunded_count,
        }
    
    except Exception as exc:
        logger.error(f"Error in cleanup_expired_bookings: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def generate_daily_reports(self):
    """
    Generate daily revenue and booking reports.
    Runs daily at midnight (00:00 IST) via Celery Beat.
    """
    try:
        from apps.booking.models import Booking
        from apps.hotels.models import Property
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        today = timezone.now().date()
        
        # Calculate daily metrics
        daily_bookings = Booking.objects.filter(
            created_at__date=today,
            status__in=['confirmed', 'completed'],
        )
        
        total_revenue = daily_bookings.aggregate(
            total=Sum('total_price')
        )['total'] or 0
        
        booking_count = daily_bookings.count()
        unique_users = daily_bookings.values('user').distinct().count()
        
        # Cache report for dashboard access
        report_key = f'report:daily:{today.isoformat()}'
        report_data = {
            'date': today.isoformat(),
            'bookings': booking_count,
            'revenue': float(total_revenue),
            'unique_users': unique_users,
            'avg_booking_value': float(total_revenue / booking_count) if booking_count > 0 else 0,
        }
        
        cache.set(report_key, report_data, 86400 * 30)  # Keep for 30 days
        
        logger.info(
            f"Daily report generated for {today}: "
            f"{booking_count} bookings, ₹{total_revenue} revenue",
            extra=report_data,
        )
        return report_data
    
    except Exception as exc:
        logger.error(f"Error in generate_daily_reports: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)


@shared_task(bind=True, max_retries=2)
def send_booking_confirmation_email(self, booking_id):
    """
    Send booking confirmation email asynchronously.
    Called after successful booking payment.
    """
    try:
        from apps.booking.models import Booking
        from django.core.mail import send_mail
        from django.conf import settings
        
        booking = Booking.objects.get(id=booking_id)
        
        email_content = f"""
        Your booking has been confirmed!
        
        Booking ID: {booking.id}
        Property: {booking.property.name if hasattr(booking, 'property') else 'N/A'}
        Total Price: ₹{booking.total_price}
        Status: {booking.status}
        
        Check your dashboard for more details.
        """
        
        send_mail(
            subject=f'Booking Confirmed - {booking.id}',
            message=email_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.user.email],
            fail_silently=False,
        )
        
        logger.info(f"Confirmation email sent for booking {booking_id}")
        return {'status': 'email_sent', 'booking_id': booking_id}
    
    except Exception as exc:
        logger.error(f"Error sending confirmation email for {booking_id}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def update_search_cache(query_params):
    """
    Update hotel search results in cache.
    Called when new properties are added or prices change.
    """
    try:
        from apps.hotels.models import Property
        from django.core.cache import cache
        import hashlib
        
        # Generate cache key from query params
        params_str = str(sorted(query_params.items()))
        cache_key = f"search:{hashlib.md5(params_str.encode()).hexdigest()}"
        
        # Invalidate cache
        cache.delete(cache_key)
        
        logger.debug(f"Invalidated search cache: {cache_key}")
        return {'cache_key': cache_key, 'invalidated': True}
    
    except Exception as exc:
        logger.error(f"Error updating search cache: {str(exc)}")
        return {'error': str(exc)}


@shared_task
def sync_operator_inventory(operator_id, resource_type):
    """
    Synchronize operator inventory (buses, cabs, packages) with cache.
    Ensures real-time availability across the system.
    """
    try:
        from django.core.cache import cache
        
        cache_key = f"inventory:{resource_type}:{operator_id}"
        
        if resource_type == 'bus':
            from buses.models import Bus
            buses = Bus.objects.filter(operator_id=operator_id).values(
                'id', 'bus_number', 'total_seats', 'available_seats', 'is_active'
            )
            cache.set(cache_key, list(buses), 300)  # 5 min TTL
        
        elif resource_type == 'cab':
            from cabs.models import Cab
            cabs = Cab.objects.filter(owner_id=operator_id).values(
                'id', 'registration_number', 'base_fare', 'rate_per_km', 'is_active'
            )
            cache.set(cache_key, list(cabs), 300)
        
        elif resource_type == 'package':
            from apps.packages.models import Package
            packages = Package.objects.filter(provider_id=operator_id).values(
                'id', 'name', 'price', 'duration_days', 'is_active'
            )
            cache.set(cache_key, list(packages), 300)
        
        logger.debug(f"Synced {resource_type} inventory for operator {operator_id}")
        return {'synced': True, 'resource_type': resource_type}
    
    except Exception as exc:
        logger.error(f"Error syncing inventory: {str(exc)}")
        return {'error': str(exc)}


@shared_task(bind=True, max_retries=3)
def sync_supplier_inventory(self, property_id, supplier_name):
    """
    Real inventory sync with supplier via adapter.
    Runs periodically for each channel manager source.
    """
    try:
        from apps.hotels.models import Property
        from apps.hotels.inventory import InventorySource
        from apps.hotels.supplier_adapters import SupplierAdapterFactory
        from core.logging_service import OperationLogger
        from datetime import datetime, timedelta
        
        property_obj = Property.objects.get(id=property_id)
        inventory = InventorySource.objects.get(property=property_obj, source_type=supplier_name)
        
        # Create adapter
        adapter = SupplierAdapterFactory.create(
            supplier_name=supplier_name,
            supplier_id=inventory.external_supplier_id,
            api_key=property_obj.supplier_api_key if hasattr(property_obj, 'supplier_api_key') else ''
        )
        
        if not adapter:
            raise ValueError(f"No adapter available for {supplier_name}")
        
        # Authenticate
        if not adapter.authenticate():
            raise ValueError(f"Authentication failed for {supplier_name}")
        
        # Fetch inventory
        end_date = (timezone.now() + timedelta(days=90)).strftime('%Y-%m-%d')
        start_date = timezone.now().strftime('%Y-%m-%d')
        
        supplier_data = adapter.fetch_inventory(start_date, end_date)
        supplier_rates = adapter.fetch_rates(inventory.external_inventory_id)
        
        # Update local inventory
        if supplier_data:
            inventory.supplier_inventory = supplier_data.get('available_rooms', 0)
            inventory.available_rooms = supplier_data.get('available_rooms', 0)
        
        if supplier_rates:
            inventory.supplier_price = supplier_rates.get('base_rate', inventory.supplier_price)
        
        # Mark sync successful
        inventory.mark_sync_success()
        
        # Log operation
        OperationLogger.log_operation(
            operation_type='inventory_sync',
            status='success',
            details={
                'property_id': property_id,
                'supplier': supplier_name,
                'rooms_synced': inventory.available_rooms,
                'supplier_price': str(inventory.supplier_price),
                'timestamp': timezone.now().isoformat()
            }
        )
        
        logger.info(f"Synced {supplier_name} inventory for property {property_id}: "
                   f"{inventory.available_rooms} rooms")
        
        return {
            'property_id': property_id,
            'supplier': supplier_name,
            'status': 'success',
            'rooms_synced': inventory.available_rooms,
        }
    
    except Exception as exc:
        logger.error(f"Error syncing {supplier_name} inventory for property {property_id}: {str(exc)}")
        
        # Mark sync failed
        try:
            from apps.hotels.models import Property
            from apps.hotels.inventory import InventorySource
            property_obj = Property.objects.get(id=property_id)
            inventory = InventorySource.objects.get(property=property_obj, source_type=supplier_name)
            inventory.mark_sync_failed(str(exc))
            
            # Log failure
            from core.logging_service import OperationLogger
            OperationLogger.log_operation(
                operation_type='inventory_sync',
                status='failed',
                details={
                    'property_id': property_id,
                    'supplier': supplier_name,
                    'error': str(exc),
                    'timestamp': timezone.now().isoformat()
                }
            )
        except:
            pass
        
        raise self.retry(exc=exc, countdown=300)  # Retry in 5 minutes


@shared_task(bind=True)
def reconcile_inventory_mismatches(self):
    """
    Periodic inventory reconciliation task.
    Detects and corrects mismatches between supplier and local inventory.
    """
    try:
        from apps.hotels.inventory import InventorySource, ExternalInventoryLog
        from apps.hotels.supplier_adapters import InventoryReconciliationEngine
        
        engine = InventoryReconciliationEngine()
        
        # Get all synced inventory
        synced_inventories = InventorySource.objects.filter(
            sync_status='synced'
        ).select_related('property')
        
        supplier_inventory = {}
        local_inventory = {}
        
        for inv in synced_inventories:
            supplier_inventory[inv.property_id] = {
                'available_rooms': inv.supplier_inventory,
            }
            local_inventory[inv.property_id] = {
                'available_rooms': inv.available_rooms,
            }
        
        # Run reconciliation
        all_match, mismatches = engine.reconcile(supplier_inventory, local_inventory)
        
        if not all_match:
            # Auto-correct using supplier as source of truth
            corrections = engine.auto_correct(mismatches, source_of_truth='supplier')
            
            # Log reconciliation
            from core.logging_service import OperationLogger
            OperationLogger.log_operation(
                operation_type='inventory_sync',
                status='corrected',
                details={
                    'mismatches_found': len(mismatches),
                    'mismatches_corrected': len(corrections),
                    'timestamp': timezone.now().isoformat(),
                    'details': corrections[:10]  # Log first 10 corrections
                }
            )
            
            logger.warning(f"Inventory reconciliation: {len(mismatches)} mismatches found and corrected")
        
        return {
            'mismatches_found': len(mismatches),
            'all_matched': all_match,
        }
    
    except Exception as exc:
        logger.error(f"Error in reconcile_inventory_mismatches: {str(exc)}")
        return {'error': str(exc)}
