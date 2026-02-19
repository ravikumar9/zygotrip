"""
Package Provider Dashboard Views
Production-grade views with atomic transactions and RBAC enforcement
"""
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from accounts.permissions import role_required
from accounts.selectors import user_has_role
from .models import Package, PackageCategory


@login_required
@role_required('package_provider')
def package_dashboard(request):
    """
    Package provider dashboard showing all their packages.
    RBAC: package_provider role required
    """
    provider = request.user
    packages = Package.objects.filter(provider=provider, is_active=True)
    
    stats = {
        'total_packages': packages.count(),
        'avg_rating': sum(p.rating for p in packages) / max(packages.count(), 1),
        'total_reviews': sum(p.review_count for p in packages),
        'total_value': float(sum(p.base_price for p in packages)),
    }
    
    context = {
        'packages': packages,
        'stats': stats,
    }
    return render(request, 'package_dashboard/dashboard.html', context)


@login_required
@role_required('package_provider')
@require_http_methods(["GET", "POST"])
def package_create(request):
    """
    Create new travel package for provider.
    POST creates package with atomic transaction.
    RBAC: package_provider role required
    """
    categories = PackageCategory.objects.all()
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                package = Package.objects.create(
                    provider=request.user,
                    name=request.POST.get('name'),
                    description=request.POST.get('description'),
                    category_id=request.POST.get('category_id'),
                    duration_days=int(request.POST.get('duration_days')),
                    destination=request.POST.get('destination'),
                    base_price=Decimal(request.POST.get('base_price')),
                    inclusions=request.POST.get('inclusions'),
                    exclusions=request.POST.get('exclusions'),
                    max_group_size=int(request.POST.get('max_group_size', 30)),
                    difficulty_level=request.POST.get('difficulty_level', 'easy'),
                    image_url=request.POST.get('image_url', ''),
                )
                
                messages.success(request, f'Package "{package.name}" created successfully!')
                return redirect('package:package_detail', package_id=package.id)
        except Exception as e:
            messages.error(request, f'Error creating package: {str(e)}')
    
    context = {
        'categories': categories,
    }
    return render(request, 'package_dashboard/package_form.html', context)


@login_required
@role_required('package_provider')
def package_detail(request, package_id):
    """
    View package details.
    RBAC: Provider can only view their own packages
    """
    package = get_object_or_404(Package, id=package_id, provider=request.user)
    
    context = {
        'package': package,
    }
    return render(request, 'package_dashboard/package_detail.html', context)


@login_required
@role_required('package_provider')
@require_http_methods(["POST"])
def package_update_price(request):
    """
    Update package price via AJAX with atomic lock.
    RBAC: package_provider role required
    Returns JSON response
    """
    try:
        package_id = request.POST.get('package_id')
        base_price = Decimal(request.POST.get('base_price'))
        
        # Atomic update with lock
        with transaction.atomic():
            package = Package.objects.select_for_update().get(
                id=package_id,
                provider=request.user
            )
            package.base_price = base_price
            package.save(update_fields=['base_price', 'updated_at'])
        
        return JsonResponse({
            'success': True,
            'message': 'Price updated',
            'base_price': str(package.base_price),
        })
    except Package.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Package not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@role_required('package_provider')
@require_http_methods(["POST"])
def package_activate_deactivate(request):
    """
    Activate or deactivate package.
    RBAC: package_provider role required
    """
    try:
        package_id = request.POST.get('package_id')
        is_active = request.POST.get('is_active') == 'true'
        
        with transaction.atomic():
            package = Package.objects.select_for_update().get(
                id=package_id,
                provider=request.user
            )
            package.is_active = is_active
            package.save(update_fields=['is_active', 'updated_at'])
        
        status = 'activated' if is_active else 'deactivated'
        messages.success(request, f'Package {status} successfully')
        return redirect('package:package_detail', package_id=package.id)
    except Package.DoesNotExist:
        messages.error(request, 'Package not found')
        return redirect('package:package_dashboard')


@login_required
@role_required('package_provider')
def package_list(request):
    """
    List all packages for provider with filtering.
    Supports filtering by category and difficulty level.
    """
    provider = request.user
    packages = Package.objects.filter(provider=provider).order_by('-created_at')
    
    # Filter by category
    category_id = request.GET.get('category_id') or ''
    if category_id:
        packages = packages.filter(category_id=category_id)
    
    # Filter by difficulty level
    difficulty = request.GET.get('difficulty_level') or ''
    if difficulty:
        packages = packages.filter(difficulty_level=difficulty)
    
    categories = PackageCategory.objects.all()
    
    context = {
        'packages': packages,
        'categories': categories,
        'selected_category': category_id,
        'selected_difficulty': difficulty,
    }
    return render(request, 'package_dashboard/packages_list.html', context)
