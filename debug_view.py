#!/usr/bin/env python
"""
Debug script to test Integration Settings context processor
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.context_processors import integration_settings
from settings.models import IntegrationSettings
from django.http import HttpRequest

def test_context_processor():
    """Test the integration settings context processor"""
    print("🔍 INTEGRATION SETTINGS DEBUG TEST")
    print("=" * 60)
    
    # 1. Check database settings
    print("\n📊 Database Check:")
    settings_count = IntegrationSettings.objects.count()
    active_settings = IntegrationSettings.objects.filter(is_active=True).first()
    
    print(f"   - Total settings in DB: {settings_count}")
    print(f"   - Active settings: {active_settings}")
    
    if active_settings:
        print(f"   - Settings ID: {active_settings.pk}")
        print(f"   - Meta Pixel Enabled: {active_settings.meta_pixel_enabled}")
        print(f"   - Meta Pixel ID: {active_settings.meta_pixel_id}")
        print(f"   - Updated: {active_settings.updated_at}")
    
    # 2. Test get_active_settings method
    print("\n🎯 Model Method Test:")
    model_settings = IntegrationSettings.get_active_settings()
    print(f"   - get_active_settings() result: {model_settings}")
    print(f"   - Has PK: {hasattr(model_settings, 'pk') and model_settings.pk}")
    
    # 3. Test context processor
    print("\n🔧 Context Processor Test:")
    request = HttpRequest()
    context = integration_settings(request)
    
    print(f"   - Context keys: {list(context.keys())}")
    
    for key, value in context.items():
        print(f"   - {key}:")
        if isinstance(value, str):
            print(f"     Type: String, Length: {len(value)}")
            if len(value) > 0 and len(value) < 200:
                print(f"     Content: {repr(value)}")
            elif len(value) > 0:
                print(f"     Preview: {repr(value[:100])}...")
        else:
            print(f"     Type: {type(value)}, Value: {value}")
    
    # 4. Manual script generation test
    print("\n🚀 Manual Script Generation Test:")
    if model_settings and hasattr(model_settings, 'pk') and model_settings.pk:
        try:
            header_scripts = model_settings.get_all_header_scripts()
            print(f"   - Header scripts length: {len(header_scripts)}")
            print(f"   - Contains 'Meta Pixel': {'Meta Pixel' in header_scripts}")
            print(f"   - Contains 'fbq': {'fbq' in header_scripts}")
            
            if header_scripts and len(header_scripts) > 0:
                print(f"   - First 300 chars: {repr(header_scripts[:300])}")
        except Exception as e:
            print(f"   - Error generating scripts: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_context_processor()