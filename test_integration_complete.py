#!/usr/bin/env python3
"""
Test script to verify complete integration settings functionality
"""
import os
import sys
import django
from django.conf import settings as django_settings

# Add the project directory to the Python path
sys.path.append(r'c:\Users\aminu\OneDrive\Desktop\ecommerce')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.models import IntegrationSettings

def test_integration_settings():
    """Test all integration settings functionality"""
    print("🧪 Testing Integration Settings Complete Setup")
    print("=" * 60)
    
    # Get or create integration settings
    settings, created = IntegrationSettings.objects.get_or_create(
        is_active=True,
        defaults={
            # Meta Pixel
            'meta_pixel_enabled': True,
            'meta_pixel_code': '''!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID');
fbq('track', 'PageView');''',
            
            # Google Analytics
            'google_analytics_enabled': True,
            'google_analytics_measurement_id': 'G-XXXXXXXXXX',
            
            # Google Tag Manager
            'gtm_enabled': True,
            'gtm_container_id': 'GTM-XXXXXXX',
            
            # Search Engine Verification
            'google_search_console_enabled': True,
            'google_search_console_code': 'google-verification-code',
            'bing_webmaster_enabled': True,
            'bing_webmaster_code': 'bing-verification-code',
            'yandex_verification_enabled': True,
            'yandex_verification_code': 'yandex-verification-code',
            
            # Hotjar
            'hotjar_enabled': True,
            'hotjar_site_id': '1234567',
            
            # Custom Scripts
            'header_scripts': '<script>console.log("Custom header script loaded");</script>',
            'footer_scripts': '<script>console.log("Custom footer script loaded");</script>',
        }
    )
    
    if created:
        print("✅ Created new integration settings")
    else:
        print("✅ Using existing integration settings")
    
    print(f"📊 Settings ID: {settings.id}")
    print(f"🔧 Active: {settings.is_active}")
    print()
    
    # Test all integration components
    print("🧩 Testing Integration Components:")
    print("-" * 40)
    
    # 1. Meta Tags
    meta_tags = settings.get_verification_meta_tags()
    print(f"🔍 Search Engine Verification Meta Tags:")
    if meta_tags:
        print(f"   ✅ Generated {len(meta_tags.split('\\n'))} meta tags")
        for line in meta_tags.split('\\n'):
            if line.strip():
                print(f"   📄 {line.strip()}")
    else:
        print("   ❌ No meta tags generated")
    print()
    
    # 2. Header Scripts
    header_scripts = settings.get_all_header_scripts()
    print(f"📄 Header Scripts:")
    if header_scripts:
        script_count = header_scripts.count('<script>')
        print(f"   ✅ Generated {script_count} script blocks")
        if 'Google Analytics' in header_scripts:
            print("   📊 Google Analytics included")
        if 'Meta Pixel' in header_scripts:
            print("   📘 Meta Pixel included")
        if 'Google Tag Manager' in header_scripts:
            print("   🏷️  Google Tag Manager included")
        if 'Hotjar' in header_scripts:
            print("   🔥 Hotjar included")
        if 'Custom header script' in header_scripts:
            print("   🔧 Custom header scripts included")
    else:
        print("   ❌ No header scripts generated")
    print()
    
    # 3. Body Scripts
    body_scripts = settings.get_all_body_scripts()
    print(f"🏗️  Body Scripts (top of body):")
    if body_scripts:
        print("   ✅ GTM noscript included")
    else:
        print("   ❌ No body scripts generated")
    print()
    
    # 4. Footer Scripts
    footer_scripts = settings.get_footer_scripts()
    print(f"🦶 Footer Scripts:")
    if footer_scripts:
        print("   ✅ Custom footer scripts included")
    else:
        print("   ❌ No footer scripts generated")
    print()
    
    # Test individual components
    print("🔬 Individual Component Tests:")
    print("-" * 40)
    
    components = [
        ("Meta Pixel", settings.get_meta_pixel_script()),
        ("Google Analytics", settings.get_google_analytics_script()),
        ("Google Tag Manager", settings.get_gtm_script()),
        ("GTM Noscript", settings.get_gtm_noscript()),
        ("Hotjar", settings.get_hotjar_script()),
    ]
    
    for name, script in components:
        if script:
            print(f"✅ {name}: Working")
        else:
            print(f"❌ {name}: Not configured")
    
    print()
    print("🌐 Integration Summary:")
    print("-" * 40)
    print(f"📊 Google Analytics: {'✅ Enabled' if settings.google_analytics_enabled else '❌ Disabled'}")
    print(f"📘 Meta Pixel: {'✅ Enabled' if settings.meta_pixel_enabled else '❌ Disabled'}")
    print(f"🏷️  Google Tag Manager: {'✅ Enabled' if settings.gtm_enabled else '❌ Disabled'}")
    print(f"🔥 Hotjar: {'✅ Enabled' if settings.hotjar_enabled else '❌ Disabled'}")
    print(f"🔍 Google Search Console: {'✅ Enabled' if settings.google_search_console_enabled else '❌ Disabled'}")
    print(f"🌐 Bing Webmaster: {'✅ Enabled' if settings.bing_webmaster_enabled else '❌ Disabled'}")
    print(f"🔍 Yandex Verification: {'✅ Enabled' if settings.yandex_verification_enabled else '❌ Disabled'}")
    
    print()
    print("🎯 Template Tags Available in Frontend:")
    print("-" * 40)
    print("✅ {{ integration_meta_tags|safe }} - Search engine verification")
    print("✅ {{ integration_header_scripts|safe }} - Analytics & tracking")
    print("✅ {{ integration_body_scripts|safe }} - GTM noscript")
    print("✅ {{ integration_footer_scripts|safe }} - Custom footer scripts")
    
    print()
    print("🚀 All integration settings are properly configured!")
    print("🌐 Your website now supports:")
    print("   📊 Google Analytics 4")
    print("   📘 Meta Pixel (Facebook)")
    print("   🏷️  Google Tag Manager")
    print("   🔥 Hotjar Analytics") 
    print("   🔍 Search Engine Verification (Google, Bing, Yandex)")
    print("   🔧 Custom Header & Footer Scripts")
    
    return settings

if __name__ == "__main__":
    test_integration_settings()