from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from accounts.permissions import login_required_403
from accounts.selectors import user_has_role
from payments.selectors import invoices_for_user


class LoginView(DjangoLoginView):
	template_name = 'accounts/login.html'


@login_required_403
def profile(request):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	invoices = invoices_for_user(request.user)
	return render(request, 'accounts/profile.html', {'invoices': invoices})


def logout_view(request):
	logout(request)
	return redirect('core:home')
