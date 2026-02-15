from decimal import Decimal
from django.db import transaction
from .models import Wallet, WalletTransaction


def get_or_create_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


def apply_wallet_payment(wallet, amount, reference=''):
    amount = Decimal(amount)
    with transaction.atomic():
        wallet.refresh_from_db()
        usable = min(wallet.balance, amount)
        wallet.balance = wallet.balance - usable
        wallet.save(update_fields=['balance', 'updated_at'])
        if usable > 0:
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=usable,
                type=WalletTransaction.TYPE_DEBIT,
                reference=reference,
            )
    return usable


def credit_wallet(wallet, amount, reference=''):
    amount = Decimal(amount)
    with transaction.atomic():
        wallet.refresh_from_db()
        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=['balance', 'updated_at'])
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            type=WalletTransaction.TYPE_CREDIT,
            reference=reference,
        )
    return wallet


def refund_wallet(wallet, amount, reference=''):
    amount = Decimal(amount)
    with transaction.atomic():
        wallet.refresh_from_db()
        wallet.balance = wallet.balance + amount
        wallet.save(update_fields=['balance', 'updated_at'])
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            type=WalletTransaction.TYPE_REFUND,
            reference=reference,
        )
    return wallet
