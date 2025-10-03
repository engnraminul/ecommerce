#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_project.settings")
django.setup()

from django.urls import resolve, reverse
from django.urls.exceptions import NoReverseMatch

# Test if the URL is properly configured
try:
    url = reverse('get_checkout_customization')
    print(f"✅ URL reverse works: {url}")
except NoReverseMatch:
    print("❌ URL name 'get_checkout_customization' not found")

# Test URL resolution
try:
    resolver = resolve('/api/v1/checkout-customization/')
    print(f"✅ URL resolves to: {resolver.func}")
    print(f"   View name: {resolver.view_name}")
    print(f"   Namespaces: {resolver.namespaces}")
except Exception as e:
    print(f"❌ URL resolution failed: {e}")

# List all URL patterns
from ecommerce_project.urls import urlpatterns
print(f"\nTotal URL patterns: {len(urlpatterns)}")

# Check if our API endpoint is in the patterns
found = False
for pattern in urlpatterns:
    if hasattr(pattern, 'pattern') and 'api/v1/' in str(pattern.pattern):
        print(f"Found API pattern: {pattern.pattern}")
        # Check if it includes our checkout-customization
        if hasattr(pattern, 'url_patterns') or hasattr(pattern, 'urlconf_name'):
            found = True

if not found:
    print("❌ API v1 pattern not properly configured")