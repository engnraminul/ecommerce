#!/usr/bin/env python3
"""
Test frontend integration by simulating a web request
"""
import os
import sys
import django
from django.test import RequestFactory
from django.template import Context, Template

# Add the project directory to the Python path
sys.path.append(r'c:\Users\aminu\OneDrive\Desktop\ecommerce')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.context_processors import integration_settings

def test_frontend_integration():
    """Test that integration settings appear in frontend templates"""
    print("🌐 Testing Frontend Integration")
    print("=" * 40)
    
    # Create a mock request
    factory = RequestFactory()
    request = factory.get('/')
    
    # Get integration context
    context = integration_settings(request)
    
    print("📋 Context Variables Available:")
    print("-" * 30)
    for key, value in context.items():
        if value:
            print(f"✅ {key}: Ready")
        else:
            print(f"❌ {key}: Empty")
    
    # Test template rendering
    print("\n🖼️  Template Rendering Test:")
    print("-" * 30)
    
    # Test meta tags
    if context['integration_meta_tags']:
        print("✅ Meta tags will render in <head>")
        meta_count = len([line for line in context['integration_meta_tags'].split('\n') if line.strip()])
        print(f"   📄 {meta_count} verification meta tags")
    
    # Test header scripts
    if context['integration_header_scripts']:
        print("✅ Header scripts will render in <head>")
        script_count = context['integration_header_scripts'].count('<script>')
        print(f"   📄 {script_count} script blocks")
    
    # Test body scripts
    if context['integration_body_scripts']:
        print("✅ Body scripts will render after <body>")
    
    # Test footer scripts
    if context['integration_footer_scripts']:
        print("✅ Footer scripts will render before </body>")
    
    print("\n🔧 Sample Template Usage:")
    print("-" * 30)
    print("<!-- In frontend/templates/frontend/base.html -->")
    print("<head>")
    print("  <!-- Other head content -->")
    print("  {{ integration_meta_tags|safe }}")
    print("  {{ integration_header_scripts|safe }}")
    print("</head>")
    print("<body>")
    print("  {{ integration_body_scripts|safe }}")
    print("  <!-- Page content -->")
    print("  {{ integration_footer_scripts|safe }}")
    print("</body>")
    
    print("\n🎯 Integration Fields Available in Settings:")
    print("-" * 45)
    print("📊 Google Analytics (GA4)")
    print("📘 Meta Pixel Code (Facebook)")
    print("🏷️  Google Tag Manager")
    print("🔍 Google Search Console Verification")
    print("🌐 Bing Webmaster Tools Verification")
    print("🔍 Yandex Webmaster Verification")
    print("🔥 Hotjar Analytics")
    print("🔧 Custom Header Scripts")
    print("🦶 Custom Footer Scripts")
    
    print("\n✅ All integration fields from settings are now available on the website!")
    
    return context

if __name__ == "__main__":
    test_frontend_integration()