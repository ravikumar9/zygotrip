from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from apps.accounts.selectors import user_has_role
from django.contrib.auth.decorators import login_required
from apps.payments.models import Payment
from apps.wallet.models import Wallet


@login_required
def dashboard(request):
	if not user_has_role(request.user, 'finance_admin'):
		raise PermissionDenied
	payments = Payment.objects.order_by('-created_at')[:20]
	wallets = Wallet.objects.order_by('-updated_at')[:20]
	return render(request, 'dashboard_finance/dashboard.html', {'payments': payments, 'wallets': wallets})

# Create your views here.