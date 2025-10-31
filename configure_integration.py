#!/usr/bin/env python3
"""
Configure and enable integration settings with sample data
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

def configure_integration_settings():
    """Configure integration settings with sample data"""
    print("🔧 Configuring Integration Settings")
    print("=" * 50)
    
    # Get existing settings or create new
    settings = IntegrationSettings.get_active_settings()
    if not settings:
        settings = IntegrationSettings.objects.create(is_active=True)
        print("✅ Created new integration settings")
    else:
        print("✅ Using existing integration settings")
    
    # Configure Meta Pixel
    settings.meta_pixel_enabled = True
    settings.meta_pixel_code = '''!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_PIXEL_ID');
fbq('track', 'PageView');'''
    
    # Configure Google Analytics
    settings.google_analytics_enabled = True
    settings.google_analytics_measurement_id = 'G-XXXXXXXXXX'
    
    # Configure Google Tag Manager
    settings.gtm_enabled = True
    settings.gtm_container_id = 'GTM-XXXXXXX'
    
    # Configure Search Engine Verification
    settings.google_search_console_enabled = True
    settings.google_search_console_code = 'google-verification-code-123'
    settings.bing_webmaster_enabled = True
    settings.bing_webmaster_code = 'bing-verification-code-456'
    settings.yandex_verification_enabled = True
    settings.yandex_verification_code = 'yandex-verification-code-789'
    
    # Configure Hotjar
    settings.hotjar_enabled = True
    settings.hotjar_site_id = '1234567'
    
    # Configure Custom Scripts
    settings.header_scripts = '''<!-- Custom Header Scripts -->
<script>
console.log("Custom header script loaded successfully");
// Add your custom header scripts here
</script>'''
    
    settings.footer_scripts = '''<!-- Custom Footer Scripts -->
<script>
console.log("Custom footer script loaded successfully");
// Add your custom footer scripts here
</script>'''
    
    # Save settings
    settings.save()
    
    print(f"📊 Settings saved with ID: {settings.id}")
    
    # Test all components
    print("\n🧩 Testing All Components:")
    print("-" * 40)
    
    # Meta Tags
    meta_tags = settings.get_verification_meta_tags()
    if meta_tags:
        print("✅ Search Engine Verification Meta Tags:")
        for line in meta_tags.split('\n'):
            if line.strip():
                print(f"   📄 {line.strip()}")
    
    # Header Scripts
    header_scripts = settings.get_all_header_scripts()
    if header_scripts:
        script_count = header_scripts.count('<script>')
        print(f"✅ Header Scripts: {script_count} script blocks generated")
    
    # Body Scripts
    body_scripts = settings.get_all_body_scripts()
    if body_scripts:
        print("✅ Body Scripts: GTM noscript generated")
    
    # Footer Scripts  
    footer_scripts = settings.get_footer_scripts()
    if footer_scripts:
        print("✅ Footer Scripts: Custom scripts generated")
    
    print("\n🎯 Integration Status:")
    print("-" * 30)
    print(f"📊 Google Analytics: {'✅ Enabled' if settings.google_analytics_enabled else '❌ Disabled'}")
    print(f"📘 Meta Pixel: {'✅ Enabled' if settings.meta_pixel_enabled else '❌ Disabled'}")
    print(f"🏷️  Google Tag Manager: {'✅ Enabled' if settings.gtm_enabled else '❌ Disabled'}")
    print(f"🔥 Hotjar: {'✅ Enabled' if settings.hotjar_enabled else '❌ Disabled'}")
    print(f"🔍 Google Search Console: {'✅ Enabled' if settings.google_search_console_enabled else '❌ Disabled'}")
    print(f"🌐 Bing Webmaster: {'✅ Enabled' if settings.bing_webmaster_enabled else '❌ Disabled'}")
    print(f"🔍 Yandex Verification: {'✅ Enabled' if settings.yandex_verification_enabled else '❌ Disabled'}")
    
    print("\n🚀 Configuration Complete!")
    print("🌐 All tracking codes are now active on your website")
    print("📝 Remember to update the IDs with your actual values:")
    print("   - Meta Pixel ID")
    print("   - Google Analytics Measurement ID")
    print("   - Google Tag Manager Container ID")
    print("   - Search engine verification codes")
    print("   - Hotjar Site ID")
    
    return settings

if __name__ == "__main__":
    configure_integration_settings()