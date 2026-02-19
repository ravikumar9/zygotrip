from decimal import Decimal
from django.db import transaction
from .models import Wallet, WalletTransaction


def get_or_create_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def apply_wallet_payment(wallet, amount, reference_id='', description=''):
    """Debit wallet for payment (booking, etc)."""
    amount = Decimal(str(amount))
    with transaction.atomic():
        wallet.refresh_from_db()
        
        if wallet.balance < amount:
            # Insufficient balance
            return {
                'success': False,
                'message': 'Insufficient wallet balance',
                'amount_debited': Decimal('0'),
            }
        
        wallet.balance = wallet.balance - amount
        wallet.save(update_fields=['balance', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=WalletTransaction.TRANSACTION_TYPE_DEBIT,
            status=WalletTransaction.STATUS_COMPLETED,
            description=description or 'Payment deducted',
            reference_id=reference_id,
        )
        
        return {
            'success': True,
            'message': 'Payment processed',
            'amount_debited': amount,
        }


def credit_wallet(wallet, amount, reference_id='', description='', status='completed'):
    """Credit wallet for refund, settlement, or promo."""
    amount = Decimal(str(amount))
    with transaction.atomic():
        wallet.refresh_from_db()
        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=['balance', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=WalletTransaction.TRANSACTION_TYPE_CREDIT,
            status=status,
            description=description or 'Amount credited',
            reference_id=reference_id,
        )
        
        return {
            'success': True,
            'message': 'Amount credited to wallet',
            'amount_credited': amount,
        }


def refund_wallet(wallet, amount, reference_id='', description=''):
    """Refund amount to wallet (booking cancellation, etc)."""
    amount = Decimal(str(amount))
    with transaction.atomic():
        wallet.refresh_from_db()
        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=['balance', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=WalletTransaction.TRANSACTION_TYPE_REFUND,
            status=WalletTransaction.STATUS_COMPLETED,
            description=description or 'Refund processed',
            reference_id=reference_id,
        )
        
        return {
            'success': True,
            'message': 'Refund processed',
            'amount_refunded': amount,
        }


def get_wallet_balance(user):
    """Get current wallet balance for user."""
    try:
        wallet = Wallet.objects.get(user=user)
        return wallet.balance
    except Wallet.DoesNotExist:
        return Decimal('0.00')


def get_transactions_history(user, limit=20):
    """Get recent wallet transactions for user."""
    try:
        wallet = Wallet.objects.get(user=user)
        return wallet.transactions.all()[:limit]
    except Wallet.DoesNotExist:
        return []
