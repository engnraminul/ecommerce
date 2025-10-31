#!/usr/bin/env python
"""
Debug script for integration settings
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.models import IntegrationSettings
from settings.context_processors import integration_settings
from django.http import HttpRequest

def debug_integration():
    print("=== Debugging Integration Settings ===\n")
    
    # Check existing settings
    all_settings = IntegrationSettings.objects.all()
    print(f"Total IntegrationSettings objects: {all_settings.count()}")
    
    for setting in all_settings:
        print(f"- ID {setting.id}: Active={setting.is_active}, Updated={setting.updated_at}")
    
    # Get active settings
    active = IntegrationSettings.get_active_settings()
    print(f"\nActive settings: {active}")
    
    if active:
        print(f"Active settings ID: {active.id if active.id else 'No ID'}")
        print(f"Meta Pixel Enabled: {active.meta_pixel_enabled}")
        print(f"Meta Pixel Code: {active.meta_pixel_code[:50] if active.meta_pixel_code else 'None'}...")
        print(f"GA Enabled: {active.google_analytics_enabled}")
        print(f"GA Measurement ID: {active.google_analytics_measurement_id}")
        
        # Test individual methods
        print("\n--- Testing individual methods ---")
        meta_script = active.get_meta_pixel_script()
        print(f"Meta Pixel Script: {len(meta_script)} chars")
        if meta_script:
            print(meta_script[:100] + "...")
        
        ga_script = active.get_google_analytics_script()
        print(f"GA Script: {len(ga_script)} chars")
        if ga_script:
            print(ga_script[:100] + "...")
        
        gtm_script = active.get_gtm_script()
        print(f"GTM Script: {len(gtm_script)} chars")
        
        verification_tags = active.get_verification_meta_tags()
        print(f"Verification Tags: {len(verification_tags)} chars")
        if verification_tags:
            print(verification_tags)
        
        header_scripts = active.get_all_header_scripts()
        print(f"All Header Scripts: {len(header_scripts)} chars")
        
        body_scripts = active.get_all_body_scripts()
        print(f"All Body Scripts: {len(body_scripts)} chars")
    
    # Test context processor
    print("\n--- Testing context processor ---")
    request = HttpRequest()
    context = integration_settings(request)
    
    print(f"Context keys: {list(context.keys())}")
    for key, value in context.items():
        if isinstance(value, str):
            print(f"{key}: {len(value)} chars")
        else:
            print(f"{key}: {value}")

if __name__ == '__main__':
    debug_integration()