#!/usr/bin/env python
"""
Update integration settings
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from settings.models import IntegrationSettings

# Update the existing settings
settings = IntegrationSettings.objects.get(id=2)
settings.meta_pixel_enabled = True
settings.google_analytics_enabled = True
settings.google_analytics_measurement_id = 'G-TEST123456'
settings.gtm_enabled = True
settings.gtm_container_id = 'GTM-TEST123'
settings.google_search_console_enabled = True
settings.google_search_console_code = 'test-google-verification'
settings.bing_webmaster_enabled = True
settings.bing_webmaster_code = 'test-bing-verification'
settings.yandex_verification_enabled = True
settings.yandex_verification_code = 'test-yandex-verification'
settings.hotjar_enabled = True
settings.hotjar_site_id = '123456'
settings.header_scripts = 'console.log("Header script loaded");'
settings.footer_scripts = 'console.log("Footer script loaded");'
settings.save()

print('✓ Integration settings updated successfully!')
print('✓ All tracking codes are now enabled')
print('✓ Test the frontend to see the integration in action')