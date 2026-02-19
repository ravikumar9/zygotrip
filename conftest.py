"""
Django tests configuration for pytest
"""

import os
import django
from django.conf import settings

def pytest_configure():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zygotrip.settings')
    django.setup()
