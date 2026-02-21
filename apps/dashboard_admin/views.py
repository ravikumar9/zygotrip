from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.selectors import user_has_role
from .models import PropertyApproval


def _ensure_admin(user):
	if not (user_has_role(user, 'staff_admin') or user_has_role(user, 'product_owner')):
		raise PermissionDenied


@login_required
def dashboard(request):
	_ensure_admin(request.user)
	pending = PropertyApproval.objects.filter(status=PropertyApproval.STATUS_PENDING)
	return render(request, 'dashboard_admin/dashboard.html', {'pending': pending})


@login_required
def approve_property(request, approval_id):
	_ensure_admin(request.user)
	approval = get_object_or_404(PropertyApproval, id=approval_id)
	approval.status = PropertyApproval.STATUS_APPROVED
	approval.decided_by = request.user
	approval.save(update_fields=['status', 'decided_by', 'updated_at'])
	messages.success(request, 'Property approved.')
	return redirect('dashboard_admin:dashboard')


@login_required
def reject_property(request, approval_id):
	_ensure_admin(request.user)
	approval = get_object_or_404(PropertyApproval, id=approval_id)
	approval.status = PropertyApproval.STATUS_REJECTED
	approval.decided_by = request.user
	approval.save(update_fields=['status', 'decided_by', 'updated_at'])
	messages.success(request, 'Property rejected.')
	return redirect('dashboard_admin:dashboard')

# Create your views here.