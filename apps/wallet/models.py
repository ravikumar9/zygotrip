"""Stub wallet models."""
from django.db import models


class Wallet(models.Model):
    """Stub Wallet model."""
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'wallet'

    def __str__(self):
        return f"Wallet for {self.user}"