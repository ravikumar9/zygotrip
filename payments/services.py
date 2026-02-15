from decimal import Decimal
from django.db import transaction
from booking.models import Booking, BookingStatusHistory
from wallet.services import apply_wallet_payment, get_or_create_wallet
from .models import Invoice, Payment


def process_payment(booking, use_wallet=True):
    with transaction.atomic():
        wallet = get_or_create_wallet(booking.user)
        wallet_used = Decimal('0.00')
        remaining = Decimal(booking.total_amount)
        method = Payment.METHOD_CARD
        if use_wallet:
            wallet_used = apply_wallet_payment(wallet, booking.total_amount, reference=str(booking.uuid))
            remaining = Decimal(booking.total_amount) - wallet_used
            method = Payment.METHOD_WALLET if remaining <= 0 else Payment.METHOD_MIXED
            if wallet_used == 0:
                method = Payment.METHOD_CARD
        payment = Payment.objects.create(
            booking=booking,
            amount=booking.total_amount,
            status=Payment.STATUS_PAID,
            method=method,
            wallet_used=wallet_used,
        )
        booking.status = Booking.STATUS_CONFIRMED
        booking.save(update_fields=['status', 'updated_at'])
        BookingStatusHistory.objects.create(booking=booking, status=Booking.STATUS_CONFIRMED)
        invoice = Invoice.objects.create(booking=booking, total_amount=booking.total_amount, status=Invoice.STATUS_PAID)
    return payment, invoice
