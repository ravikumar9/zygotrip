"""
Phase 4: Cancellation Policy Engine.
Owner-configurable policies with free/partial/non-refundable windows.
"""
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class CancellationPolicy(TimeStampedModel):
    """
    Per-property cancellation policy.
    Defines refund tiers based on hours remaining until check-in.

    Tiers (evaluated in order — first matching window wins):
    1. Free cancellation: full refund if cancelled >= free_cancel_hours before check-in
    2. Partial refund: partial_refund_percent if cancelled >= partial_cancel_hours before check-in
    3. Non-refundable: no refund if cancelled < non_refundable_hours before check-in
    """

    POLICY_TYPE_FLEXIBLE = 'flexible'
    POLICY_TYPE_MODERATE = 'moderate'
    POLICY_TYPE_STRICT = 'strict'
    POLICY_TYPE_NON_REFUNDABLE = 'non_refundable'
    POLICY_TYPE_CUSTOM = 'custom'

    POLICY_TYPE_CHOICES = [
        (POLICY_TYPE_FLEXIBLE, 'Flexible (Free cancel 48h+)'),
        (POLICY_TYPE_MODERATE, 'Moderate (Free cancel 24h+, 50% after)'),
        (POLICY_TYPE_STRICT, 'Strict (50% cancel 7d+, non-refundable after)'),
        (POLICY_TYPE_NON_REFUNDABLE, 'Non-Refundable'),
        (POLICY_TYPE_CUSTOM, 'Custom Policy'),
    ]

    property = models.OneToOneField(
        'hotels.Property',
        on_delete=models.CASCADE,
        related_name='cancellation_policy'
    )
    policy_type = models.CharField(
        max_length=20,
        choices=POLICY_TYPE_CHOICES,
        default=POLICY_TYPE_FLEXIBLE
    )

    # === TIER 1: Free cancellation window ===
    free_cancel_hours = models.PositiveIntegerField(
        default=48,
        help_text="Hours before check-in within which full refund applies. 0 = no free window."
    )

    # === TIER 2: Partial refund window ===
    partial_refund_enabled = models.BooleanField(
        default=True,
        help_text="If True, a partial refund window applies between tiers 1 and 3."
    )
    partial_refund_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('50.00'),
        help_text="Percentage of booking value refunded in the partial window."
    )
    partial_cancel_hours = models.PositiveIntegerField(
        default=24,
        help_text="Hours before check-in at which partial refund applies (must be < free_cancel_hours)."
    )

    # === TIER 3: Non-refundable window ===
    non_refundable_hours = models.PositiveIntegerField(
        default=0,
        help_text="Cancellations within this many hours of check-in = 0% refund."
    )

    # === Platform deductions (always withheld) ===
    platform_fee_always_withheld = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('2.00'),
        help_text="Platform convenience fee % always withheld even in free cancellations."
    )

    display_note = models.CharField(
        max_length=300, blank=True,
        help_text="Human-readable policy summary shown on booking page."
    )

    class Meta:
        app_label = 'booking'

    def __str__(self):
        return f"CancelPolicy({self.property}, {self.policy_type})"

    def get_display_note(self):
        if self.display_note:
            return self.display_note
        if self.policy_type == self.POLICY_TYPE_NON_REFUNDABLE:
            return "Non-refundable — no cancellations allowed."
        if self.free_cancel_hours > 0:
            return (
                f"Free cancellation up to {self.free_cancel_hours}h before check-in. "
                f"Cancel within {self.free_cancel_hours}h: "
                f"{self.partial_refund_percent}% refund."
            )
        return "No free cancellation available."


class RefundCalculator:
    """
    Service class: computes refund amount based on policy + hours until check-in.
    Used by cancellation flow in booking views and Celery tasks.
    """

    def __init__(self, policy: CancellationPolicy, booking_total: Decimal):
        self.policy = policy
        self.booking_total = Decimal(str(booking_total))

    def compute(self, checkin_date) -> dict:
        """
        Returns a dict with:
          - refund_amount: Decimal — amount to return to customer
          - platform_fee: Decimal — amount kept by platform
          - refund_percent: Decimal — percentage refunded
          - tier: str — which refund tier was applied
          - note: str — human-readable explanation
        """
        now = timezone.now()
        if hasattr(checkin_date, 'date'):
            checkin_dt = checkin_date
        else:
            from datetime import datetime as _dt
            checkin_dt = _dt.combine(checkin_date, _dt.min.time()).replace(tzinfo=timezone.utc)

        hours_until_checkin = (checkin_dt - now).total_seconds() / 3600
        policy = self.policy
        platform_fee_amount = (self.booking_total * policy.platform_fee_always_withheld / 100).quantize(Decimal('0.01'))

        # Non-refundable policy: always 0 refund
        if policy.policy_type == CancellationPolicy.POLICY_TYPE_NON_REFUNDABLE:
            return self._result(
                refund_amount=Decimal('0.00'),
                platform_fee=platform_fee_amount,
                refund_percent=Decimal('0.00'),
                tier='non_refundable',
                note="Non-refundable booking — no refund applicable."
            )

        # Within non-refundable window
        if hours_until_checkin < policy.non_refundable_hours:
            return self._result(
                refund_amount=Decimal('0.00'),
                platform_fee=platform_fee_amount,
                refund_percent=Decimal('0.00'),
                tier='non_refundable_window',
                note=f"Cancellation within {policy.non_refundable_hours}h of check-in — no refund."
            )

        # TIER 1: Free cancellation
        if hours_until_checkin >= policy.free_cancel_hours and policy.free_cancel_hours > 0:
            gross_refund = self.booking_total - platform_fee_amount
            return self._result(
                refund_amount=max(Decimal('0.00'), gross_refund),
                platform_fee=platform_fee_amount,
                refund_percent=Decimal('100.00') - policy.platform_fee_always_withheld,
                tier='free_cancel',
                note=f"Free cancellation applied — full refund minus {policy.platform_fee_always_withheld}% platform fee."
            )

        # TIER 2: Partial refund
        if policy.partial_refund_enabled and hours_until_checkin >= policy.partial_cancel_hours:
            partial = (self.booking_total * policy.partial_refund_percent / 100).quantize(Decimal('0.01'))
            gross_refund = partial - platform_fee_amount
            return self._result(
                refund_amount=max(Decimal('0.00'), gross_refund),
                platform_fee=platform_fee_amount,
                refund_percent=policy.partial_refund_percent,
                tier='partial',
                note=f"Partial refund — {policy.partial_refund_percent}% of booking value."
            )

        # TIER 3: Non-refundable (catch-all)
        return self._result(
            refund_amount=Decimal('0.00'),
            platform_fee=platform_fee_amount,
            refund_percent=Decimal('0.00'),
            tier='non_refundable',
            note="Cancellation policy window passed — no refund applicable."
        )

    @staticmethod
    def _result(refund_amount, platform_fee, refund_percent, tier, note):
        return {
            'refund_amount': refund_amount,
            'platform_fee': platform_fee,
            'refund_percent': refund_percent,
            'tier': tier,
            'note': note,
        }
