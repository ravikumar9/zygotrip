"""
Pricing Fraud Protection Layer

Detects and blocks suspicious pricing patterns that indicate:
- Competitor price manipulation attacks
- Bulk price manipulation (rapid supplier updates)
- Suspicious demand score spikes

Guard rules:
1. Price drops >70% within 5 min → BLOCK
2. Price rises >200% within 5 min → BLOCK  
3. Same supplier sends >50 updates/min → RATE_LIMIT
4. Demand score changes >50 points in 1 min → SUSPICIOUS
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from core.models import OperationLog
from django.core.cache import cache
from django.core.exceptions import SuspiciousOperation

logger = logging.getLogger('zygotrip')


class FraudDetection(SuspiciousOperation):
    """Raised when fraudulent activity is detected"""
    pass


class RateLimitExceeded(SuspiciousOperation):
    """Raised when update rate exceeds limits"""
    pass


class PricingGuardConfig:
    """Configuration for fraud detection"""
    
    # Price change limits
    MAX_PRICE_DROP_PERCENT = 70      # Block if price drops > 70%
    MAX_PRICE_RISE_PERCENT = 200     # Block if price rises > 200%
    CHECK_WINDOW_MINUTES = 5         # Look back this many minutes
    
    # Update rate limits
    MAX_UPDATES_PER_MINUTE = 50      # Max updates from single supplier/min
    MAX_UPDATES_PER_HOUR = 1000      # Max updates from single supplier/hour
    
    # Demand score limits
    MAX_DEMAND_SPIKE = 50            # Max change in demand_score/minute
    DEMAND_CHECK_WINDOW_MINUTES = 5

    # Gradual drop detection
    GRADUAL_DROP_WINDOW_UPDATES = 100
    GRADUAL_DROP_PERCENT = 50
    GRADUAL_DROP_WINDOW_MINUTES = 60
    
    # Blacklist
    FRAUD_IP_CACHE_MINUTES = 60      # Cache suspicious IPs for 1 hour


class PricingGuard:
    """
    Detects fraudulent pricing patterns.
    
    All checks are non-blocking logging by default.
    Critical violations block the operation.
    """
    
    config = PricingGuardConfig()
    
    @staticmethod
    def _get_cache_key(prefix: str, **kwargs) -> str:
        """Generate cache key for tracking"""
        parts = [prefix]
        parts.extend(str(v) for v in kwargs.values())
        return ":".join(parts)
    
    @staticmethod
    def check_price_change(
        property_id: int,
        new_price: Decimal,
        previous_price: Decimal
    ) -> bool:
        """
        Check if price change is suspicious.
        
        Rules:
        - Block if drop > 70%
        - Block if rise > 200%
        
        Args:
            property_id: Property ID
            new_price: New proposed price
            previous_price: Previous price
        
        Returns:
            True if safe, False if suspicious
        
        Raises:
            FraudDetection: If block-level violation
        """
        
        if previous_price <= 0:
            return True  # Cannot calculate change
        
        change_percent = ((new_price - previous_price) / previous_price) * 100
        
        # Check drop
        if change_percent < -PricingGuard.config.MAX_PRICE_DROP_PERCENT:
            logger.error(
                f"FRAUD_ALERT: Property {property_id} price drop {change_percent:.1f}% "
                f"exceeds limit {PricingGuard.config.MAX_PRICE_DROP_PERCENT}%: "
                f"₹{previous_price} → ₹{new_price}"
            )
            OperationLog.objects.create(
                operation_type='fraud_triggered',
                status='failed',
                details=str({
                    'property_id': property_id,
                    'reason': 'price_drop_limit',
                    'change_percent': float(change_percent),
                    'previous_price': str(previous_price),
                    'new_price': str(new_price),
                }),
                timestamp=timezone.now(),
            )
            raise FraudDetection(
                f"Price drop {change_percent:.1f}% violates safety limits"
            )
        
        # Check rise
        if change_percent > PricingGuard.config.MAX_PRICE_RISE_PERCENT:
            logger.error(
                f"FRAUD_ALERT: Property {property_id} price rise {change_percent:.1f}% "
                f"exceeds limit {PricingGuard.config.MAX_PRICE_RISE_PERCENT}%: "
                f"₹{previous_price} → ₹{new_price}"
            )
            OperationLog.objects.create(
                operation_type='fraud_triggered',
                status='failed',
                details=str({
                    'property_id': property_id,
                    'reason': 'price_rise_limit',
                    'change_percent': float(change_percent),
                    'previous_price': str(previous_price),
                    'new_price': str(new_price),
                }),
                timestamp=timezone.now(),
            )
            raise FraudDetection(
                f"Price rise {change_percent:.1f}% violates safety limits"
            )

        # Gradual drop detection (e.g., 1% x 100)
        history_key = PricingGuard._get_cache_key(
            "price_history",
            property_id=property_id
        )
        history = cache.get(history_key, [])
        now = timezone.now()
        history.append((now.isoformat(), str(new_price)))
        # Keep only recent history within window minutes
        cutoff = now - timedelta(minutes=PricingGuard.config.GRADUAL_DROP_WINDOW_MINUTES)
        filtered = []
        for ts, price in history:
            try:
                ts_dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            if ts_dt >= cutoff:
                filtered.append((ts, price))
        history = filtered
        cache.set(history_key, history, PricingGuard.config.GRADUAL_DROP_WINDOW_MINUTES * 60)

        if len(history) >= PricingGuard.config.GRADUAL_DROP_WINDOW_UPDATES:
            first_price = Decimal(str(history[0][1]))
            if first_price > 0:
                gradual_drop = ((new_price - first_price) / first_price) * 100
                if gradual_drop < -PricingGuard.config.GRADUAL_DROP_PERCENT:
                    logger.error(
                        f"FRAUD_ALERT: Property {property_id} gradual drop {gradual_drop:.1f}% "
                        f"over {len(history)} updates"
                    )
                    OperationLog.objects.create(
                        operation_type='fraud_triggered',
                        status='failed',
                        details=str({
                            'property_id': property_id,
                            'reason': 'gradual_price_drop',
                            'change_percent': float(gradual_drop),
                            'updates': len(history),
                        }),
                        timestamp=timezone.now(),
                    )
                    raise FraudDetection(
                        f"Gradual price drop {gradual_drop:.1f}% violates safety limits"
                    )
        
        # Warn on extreme changes (80-120% range)
        if abs(change_percent) > 50:
            logger.warning(
                f"SUSPICIOUS_PRICE_CHANGE: Property {property_id} "
                f"change {change_percent:.1f}%: ₹{previous_price} → ₹{new_price}"
            )
        
        return True
    
    @staticmethod
    def check_update_rate(supplier_name: str, supplier_id: str, client_ip: str = None) -> bool:
        """
        Check if supplier is sending updates too frequently.
        
        Rules:
        - Block if >50 updates/minute from same supplier
        - Block if >1000 updates/hour from same supplier
        
        Args:
            supplier_name: Supplier identifier
            supplier_id: Supplier's property ID
        
        Returns:
            True if safe, False if rate-limited
        
        Raises:
            RateLimitExceeded: If rate limit violated
        """
        
        supplier_key = f"{supplier_name}:{supplier_id}"
        
        # Check per-minute rate
        minute_key = PricingGuard._get_cache_key(
            "supplier_updates_min",
            supplier=supplier_key,
            minute=timezone.now().minute
        )
        
        minute_count = cache.get(minute_key, 0)
        minute_count += 1
        cache.set(minute_key, minute_count, 60)  # 1 minute TTL
        
        if minute_count > PricingGuard.config.MAX_UPDATES_PER_MINUTE:
            logger.error(
                f"FRAUD_ALERT: Supplier {supplier_key} exceeds rate limit "
                f"{minute_count} updates/min (max: {PricingGuard.config.MAX_UPDATES_PER_MINUTE})"
            )
            if client_ip:
                ip_key = PricingGuard._get_cache_key("fraud_ip", ip=client_ip)
                cache.set(ip_key, True, PricingGuard.config.FRAUD_IP_CACHE_MINUTES * 60)
            OperationLog.objects.create(
                operation_type='fraud_triggered',
                status='failed',
                details=str({
                    'supplier': supplier_key,
                    'reason': 'rate_limit',
                    'minute_count': minute_count,
                    'client_ip': client_ip,
                }),
                timestamp=timezone.now(),
            )
            raise RateLimitExceeded(
                f"Supplier {supplier_name} exceeds rate limit"
            )
        
        # Check per-hour rate (warning only)
        hour_key = PricingGuard._get_cache_key(
            "supplier_updates_hour",
            supplier=supplier_key,
            hour=timezone.now().hour
        )
        
        hour_count = cache.get(hour_key, 0)
        hour_count += 1
        cache.set(hour_key, hour_count, 3600)  # 1 hour TTL
        
        if hour_count > PricingGuard.config.MAX_UPDATES_PER_HOUR:
            logger.warning(
                f"HIGH_UPDATE_RATE: Supplier {supplier_key} "
                f"{hour_count} updates/hour (threshold: {PricingGuard.config.MAX_UPDATES_PER_HOUR})"
            )
        
        return True
    
    @staticmethod
    def check_demand_spike(
        property_id: int,
        new_demand_score: int,
        previous_demand_score: int
    ) -> bool:
        """
        Check if demand score spike is suspicious.
        
        Rules:
        - Warn if change > 50 points in 1 minute
        
        Args:
            property_id: Property ID
            new_demand_score: New demand score (0-100)
            previous_demand_score: Previous demand score
        
        Returns:
            True if safe
        """
        
        change = abs(new_demand_score - previous_demand_score)
        
        if change > PricingGuard.config.MAX_DEMAND_SPIKE:
            logger.warning(
                f"SUSPICIOUS_DEMAND_SPIKE: Property {property_id} "
                f"demand changed {change} points in 1 minute: "
                f"{previous_demand_score} → {new_demand_score}"
            )
        
        return True
    
    @staticmethod
    def check_all(
        property_id: int,
        supplier_name: str,
        supplier_id: str,
        new_price: Decimal,
        previous_price: Decimal,
        new_demand_score: int = None,
        previous_demand_score: int = None,
        client_ip: str = None
    ) -> bool:
        """
        Run all fraud checks in sequence.
        
        Returns:
            True if all checks pass
        
        Raises:
            FraudDetection or RateLimitExceeded if violation
        """
        
        # Check price change
        PricingGuard.check_price_change(property_id, new_price, previous_price)
        
        # Check update rate
        PricingGuard.check_update_rate(supplier_name, supplier_id, client_ip=client_ip)
        
        # Check demand spike (optional)
        if new_demand_score is not None and previous_demand_score is not None:
            PricingGuard.check_demand_spike(
                property_id,
                new_demand_score,
                previous_demand_score
            )
        
        return True
