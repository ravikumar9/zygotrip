"""
Packages views - Minimal implementation for routing fix
Phase 1: Return HTTP 200 for all routes
Phase 2: Add selectors/services pattern
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def package_list(request):
    """Display available travel packages - minimal implementation"""
    context = {
        'packages': [],  # Temporary: empty list until models ready
        'page_title': 'Travel Packages',
    }
    return render(request, 'packages/list.html', context)


@login_required
def package_detail(request, package_id):
    """Display single package detail"""
    context = {
        'package': None,  # Temporary: placeholder
        'page_title': 'Package Details',
    }
    return render(request, 'packages/detail.html', context)


@login_required
def package_booking(request, package_id):
    """Handle package booking request"""
    context = {
        'package': None,
        'page_title': 'Book Package',
    }
    return render(request, 'packages/booking.html', context)