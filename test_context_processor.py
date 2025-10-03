#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ecommerce_project.settings")
django.setup()

from django.test import RequestFactory
from settings.context_processors import checkout_customization

def test_context_processor():
    print("Testing checkout customization context processor...")
    
    # Create a fake request
    factory = RequestFactory()
    request = factory.get('/')
    
    try:
        # Test the context processor
        context = checkout_customization(request)
        
        print(f"Context keys: {list(context.keys())}")
        
        if 'checkout_customization' in context:
            customization = context['checkout_customization']
            
            if customization:
                print("✅ Context processor working!")
                print(f"   Page title: {customization.page_title}")
                print(f"   Primary color: {customization.primary_color}")
                print(f"   Is active: {customization.is_active}")
                print(f"   ID: {customization.id}")
            else:
                print("❌ Context processor returned None")
        else:
            print("❌ checkout_customization not in context")
            
    except Exception as e:
        print(f"❌ Error in context processor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_context_processor()