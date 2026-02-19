from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.selectors import user_has_role
from payments.selectors import invoices_for_user
from booking.models import Booking
from .forms import RegisterForm, CustomAuthenticationForm
from .models import Role, UserRole


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
	bookings = Booking.objects.filter(user=request.user).select_related('property').order_by('-created_at')
	
	# Statistics
	total_bookings = bookings.count()
	confirmed_bookings = bookings.filter(status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_PAYMENT]).count()
	cancelled_bookings = bookings.filter(status=Booking.STATUS_CANCELLED).count()
	
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
		role = Role.objects.filter(code='customer').first()
		if role:
			UserRole.objects.get_or_create(user=user, role=role)
		login(request, user, backend='django.contrib.auth.backends.ModelBackend')
		return redirect('core:home')
	return render(request, 'accounts/register.html', {'form': form})
