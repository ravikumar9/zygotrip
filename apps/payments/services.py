"""Stub payments services module."""
from decimal import Decimal


def process_payment(booking=None, amount=None, payment_method=None):
    """Process a payment for a booking."""
    return {
        'status': 'success',
        'transaction_id': 'stub-txn-123',
        'amount': amount or Decimal('0.00'),
        'method': payment_method or 'credit_card'
    }