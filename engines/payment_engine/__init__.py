"""
Payment Engine - Payment processing logic
PHASE 3: Extracted from payments app
CRITICAL RULE: NO app imports - pure business logic
"""
from decimal import Decimal
from typing import Dict, Any
import uuid
import hashlib


def generate_transaction_id() -> str:
    """Generate unique transaction ID"""
    return f"TXN{uuid.uuid4().hex[:12].upper()}"


def generate_payment_reference() -> str:
    """Generate payment reference number"""
    return f"PAY{uuid.uuid4().hex[:10].upper()}"


def calculate_payment_hash(
    transaction_id: str,
    amount: Decimal,
    secret_key: str
) -> str:
    """
    Calculate payment verification hash
    
    Args:
        transaction_id: Transaction ID
        amount: Payment amount
        secret_key: Secret key for hashing
    
    Returns:
        SHA256 hash
    """
    payload = f"{transaction_id}|{amount}|{secret_key}"
    return hashlib.sha256(payload.encode()).hexdigest()


def validate_payment_amount(
    requested_amount: Decimal,
    expected_amount: Decimal,
    tolerance: Decimal = Decimal('0.01')
) -> tuple[bool, str]:
    """
    Validate payment amount matches expected
    
    Args:
        requested_amount: Amount being paid
        expected_amount: Expected payment amount
        tolerance: Acceptable difference
    
    Returns:
        (is_valid, error_message)
    """
    difference = abs(requested_amount - expected_amount)
    
    if difference > tolerance:
        return False, f"Amount mismatch: expected {expected_amount}, got {requested_amount}"
    
    if requested_amount <= 0:
        return False, "Payment amount must be greater than zero"
    
    return True, ""


def determine_payment_method_fee(
    amount: Decimal,
    payment_method: str
) -> Decimal:
    """
    Calculate payment gateway fee
    
    Args:
        amount: Payment amount
        payment_method: 'card', 'upi', 'netbanking', 'wallet'
    
    Returns:
        Fee amount
    """
    fee_rates = {
        'card': Decimal('0.02'),  # 2%
        'upi': Decimal('0.00'),   # Free
        'netbanking': Decimal('0.015'),  # 1.5%
        'wallet': Decimal('0.01')  # 1%
    }
    
    rate = fee_rates.get(payment_method, Decimal('0.02'))
    fee = amount * rate
    
    return fee.quantize(Decimal('0.01'))


def validate_payment_method(payment_method: str) -> tuple[bool, str]:
    """
    Validate payment method is supported
    
    Returns:
        (is_valid, error_message)
    """
    valid_methods = ['card', 'upi', 'netbanking', 'wallet', 'cash']
    
    if payment_method not in valid_methods:
        return False, f"Invalid payment method. Supported: {', '.join(valid_methods)}"
    
    return True, ""


def calculate_refund_amount(
    original_amount: Decimal,
    cancellation_charge: Decimal = Decimal('0.00'),
    processing_fee: Decimal = Decimal('0.00')
) -> Dict[str, Decimal]:
    """
    Calculate refund amount after deductions
    
    Args:
        original_amount: Original payment amount
        cancellation_charge: Cancellation penalty
        processing_fee: Refund processing fee
    
    Returns:
        Dict with original, deductions, refund
    """
    total_deductions = cancellation_charge + processing_fee
    refund = max(Decimal('0.00'), original_amount - total_deductions)
    
    return {
        'original_amount': original_amount,
        'cancellation_charge': cancellation_charge,
        'processing_fee': processing_fee,
        'total_deductions': total_deductions,
        'refund_amount': refund.quantize(Decimal('0.01'))
    }


def determine_payment_status(
    gateway_status: str
) -> str:
    """
    Map gateway status to internal status
    
    Args:
        gateway_status: Status from payment gateway
    
    Returns:
        'pending', 'processing', 'completed', 'failed', 'refunded'
    """
    status_map = {
        'success': 'completed',
        'captured': 'completed',
        'authorized': 'processing',
        'pending': 'pending',
        'failed': 'failed',
        'declined': 'failed',
        'refunded': 'refunded',
        'partial_refund': 'refunded'
    }
    
    return status_map.get(gateway_status.lower(), 'pending')


def is_payment_final(status: str) -> bool:
    """Check if payment status is final (no further changes)"""
    final_statuses = ['completed', 'failed', 'refunded']
    return status in final_statuses


def calculate_split_payment(
    total_amount: Decimal,
    split_count: int
) -> list[Decimal]:
    """
    Split payment into equal parts
    
    Args:
        total_amount: Total to split
        split_count: Number of splits
    
    Returns:
        List of split amounts
    """
    if split_count <= 0:
        return [total_amount]
    
    per_split = (total_amount / split_count).quantize(Decimal('0.01'))
    splits = [per_split] * split_count
    
    # Adjust last split to account for rounding
    actual_total = sum(splits)
    difference = total_amount - actual_total
    splits[-1] += difference
    
    return splits