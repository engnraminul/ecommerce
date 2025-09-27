#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.utils import timezone
from django.conf import settings

def test_timezone_configuration():
    """Test that the timezone is properly configured for Dhaka, Bangladesh"""
    
    print("=== Timezone Configuration Test ===")
    print(f"Django TIME_ZONE setting: {settings.TIME_ZONE}")
    print(f"Django USE_TZ setting: {settings.USE_TZ}")
    
    # Get current time in various formats
    utc_now = datetime.utcnow()
    django_now = timezone.now()
    
    print(f"\nCurrent times:")
    print(f"UTC time: {utc_now}")
    print(f"Django timezone.now(): {django_now}")
    
    # Test if timezone is correctly set
    if settings.TIME_ZONE == 'Asia/Dhaka':
        print("✓ Django timezone is correctly set to Asia/Dhaka")
    else:
        print("✗ Django timezone is not set to Asia/Dhaka")
    
    # Test USE_TZ setting
    if settings.USE_TZ:
        print("✓ Django USE_TZ is enabled (timezone-aware)")
    else:
        print("✗ Django USE_TZ is disabled")
    
    # Test date formatting for JavaScript compatibility
    js_date = django_now.strftime('%Y-%m-%d')
    js_datetime = django_now.strftime('%Y-%m-%d %H:%M:%S')
    print(f"JavaScript date format: {js_date}")
    print(f"JavaScript datetime format: {js_datetime}")
    
    print("\n=== Test completed ===")

if __name__ == '__main__':
    test_timezone_configuration()