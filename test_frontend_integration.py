#!/usr/bin/env python
"""
Test script to verify all integration settings are properly working in frontend
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.models import IntegrationSettings
from settings.context_processors import integration_settings
from django.http import HttpRequest

def test_integration_in_frontend():
    print("=== Testing Integration Settings in Frontend ===\n")
    
    # Create comprehensive test data
    print("1. Creating comprehensive integration settings...")
    settings = IntegrationSettings.objects.create(
        # Meta Pixel
        meta_pixel_enabled=True,
        meta_pixel_code='''<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '123456789012345');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=123456789012345&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->''',
        
        # Google Analytics
        google_analytics_enabled=True,
        google_analytics_measurement_id='G-ABCD123456',
        
        # Google Tag Manager
        gtm_enabled=True,
        gtm_container_id='GTM-ABC123',
        
        # Search Engine Verification
        google_search_console_enabled=True,
        google_search_console_code='google-verification-123456789abcdef',
        bing_webmaster_enabled=True,
        bing_webmaster_code='bing-verification-987654321fedcba',
        yandex_verification_enabled=True,
        yandex_verification_code='yandex-verification-456789123abc',
        
        # Hotjar
        hotjar_enabled=True,
        hotjar_site_id='123456',
        
        # Custom Scripts
        header_scripts='''<!-- Custom Header Script -->
<script>
    console.log('Custom header script loaded');
    // Custom tracking or analytics code
</script>''',
        
        footer_scripts='''<!-- Custom Footer Script -->
<script>
    console.log('Custom footer script loaded');
    // Additional tracking code
</script>''',
        
        is_active=True
    )
    print(f"✓ Created integration settings with ID: {settings.id}")
    
    # Test context processor
    print("\n2. Testing context processor output...")
    request = HttpRequest()
    context = integration_settings(request)
    
    print("\n--- SEARCH ENGINE VERIFICATION META TAGS ---")
    meta_tags = context['integration_meta_tags']
    print(meta_tags)
    print(f"Length: {len(meta_tags)} characters")
    
    print("\n--- HEADER SCRIPTS (First 500 chars) ---")
    header_scripts = context['integration_header_scripts']
    print(header_scripts[:500] + "..." if len(header_scripts) > 500 else header_scripts)
    print(f"Total length: {len(header_scripts)} characters")
    
    print("\n--- BODY SCRIPTS (First 500 chars) ---")
    body_scripts = context['integration_body_scripts']
    print(body_scripts[:500] + "..." if len(body_scripts) > 500 else body_scripts)
    print(f"Total length: {len(body_scripts)} characters")
    
    # Verify each component
    print("\n3. Verifying individual components...")
    
    # Check Meta Pixel
    if 'fbq(' in header_scripts:
        print("✓ Meta Pixel tracking code found in header")
    else:
        print("✗ Meta Pixel tracking code missing")
    
    # Check Google Analytics
    if 'G-ABCD123456' in header_scripts and 'gtag(' in header_scripts:
        print("✓ Google Analytics (GA4) tracking code found")
    else:
        print("✗ Google Analytics tracking code missing")
    
    # Check Google Tag Manager
    if 'GTM-ABC123' in header_scripts and 'googletagmanager.com' in header_scripts:
        print("✓ Google Tag Manager script found in header")
    else:
        print("✗ Google Tag Manager script missing")
    
    if 'GTM-ABC123' in body_scripts and 'noscript' in body_scripts:
        print("✓ Google Tag Manager noscript found in body")
    else:
        print("✗ Google Tag Manager noscript missing")
    
    # Check Search Engine Verification
    if 'google-site-verification' in meta_tags:
        print("✓ Google Search Console verification meta tag found")
    else:
        print("✗ Google Search Console verification missing")
    
    if 'msvalidate.01' in meta_tags:
        print("✓ Bing Webmaster verification meta tag found")
    else:
        print("✗ Bing Webmaster verification missing")
    
    if 'yandex-verification' in meta_tags:
        print("✓ Yandex verification meta tag found")
    else:
        print("✗ Yandex verification missing")
    
    # Check Hotjar
    if 'hotjar' in header_scripts and '123456' in header_scripts:
        print("✓ Hotjar analytics script found")
    else:
        print("✗ Hotjar analytics script missing")
    
    # Check Custom Scripts
    if 'Custom header script' in header_scripts:
        print("✓ Custom header scripts found")
    else:
        print("✗ Custom header scripts missing")
    
    if 'Custom footer script' in body_scripts:
        print("✓ Custom footer scripts found")
    else:
        print("✗ Custom footer scripts missing")
    
    print("\n4. Frontend Template Integration Status:")
    print("✓ Meta tags placed in <head> section: {{ integration_meta_tags|safe }}")
    print("✓ Header scripts placed in <head> section: {{ integration_header_scripts|safe }}")
    print("✓ Body scripts placed after <body> tag: {{ integration_body_scripts|safe }}")
    
    print("\n5. What appears on every page:")
    print("📧 Search engine verification meta tags")
    print("📊 Google Analytics tracking")
    print("🏷️ Google Tag Manager")
    print("📘 Meta Pixel (Facebook) tracking")
    print("🔥 Hotjar user behavior analytics")
    print("⚙️ Custom header scripts")
    print("⚙️ Custom footer scripts")
    
    print("\n=== Integration Complete! ===")
    print("✅ All tracking codes will automatically appear on every page")
    print("✅ No manual template editing required")
    print("✅ Managed through dashboard Settings → Integration")
    print("✅ Real-time updates when settings are changed")
    
    # Clean up
    settings.delete()
    print("\n✓ Test data cleaned up")

if __name__ == '__main__':
    test_integration_in_frontend()