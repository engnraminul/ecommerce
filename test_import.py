#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_project.settings")
django.setup()

try:
    from dashboard.views import get_checkout_customization
    print("✅ Successfully imported get_checkout_customization")
    print(f"Function: {get_checkout_customization}")
    print(f"Type: {type(get_checkout_customization)}")
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Other error: {e}")