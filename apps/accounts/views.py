from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.accounts.selectors import user_has_role, get_customer_bookings, get_booking_stats
from apps.payments.selectors import invoices_for_user
from .forms import RegisterForm, CustomAuthenticationForm
from .services import assign_customer_role


class LoginView(DjangoLoginView):
	template_name = 'accounts/login.html'
	form_class = CustomAuthenticationForm
	redirect_authenticated_user = True

	def get_success_url(self):
		return reverse_lazy('core:home')


@login_required
def profile(request):
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	invoices = invoices_for_user(request.user)
	return render(request, 'accounts/profile.html', {'invoices': invoices})


@login_required
def customer_dashboard(request):
	"""Customer dashboard - shows bookings and booking history"""
	if not user_has_role(request.user, 'customer'):
		raise PermissionDenied
	
	# Get customer's bookings
	bookings = get_customer_bookings(request.user)
	
	# Statistics
	total_bookings, confirmed_bookings, cancelled_bookings = get_booking_stats(bookings)
	
	context = {
		'bookings': bookings,
		'total_bookings': total_bookings,
		'confirmed_bookings': confirmed_bookings,
		'cancelled_bookings': cancelled_bookings,
	}
	
	return render(request, 'accounts/customer_dashboard.html', context)


def logout_view(request):
	logout(request)
	return redirect('core:home')


def register_view(request):
	form = RegisterForm(request.POST or None)
	if request.method == 'POST' and form.is_valid():
		user = form.save()
		assign_customer_role(user)
		login(request, user, backend='django.contrib.auth.backends.ModelBackend')
		return redirect('core:home')
	return render(request, 'accounts/register.html', {'form': form})