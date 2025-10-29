"""
Update contact settings to include latitude and longitude fields
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from contact.models import ContactSetting

# Get the contact settings
contact_setting = ContactSetting.objects.filter(key='contact_details').first()

if contact_setting:
    print("Current settings:")
    print(f"  Business: {contact_setting.value.get('business_name')}")
    print(f"  Address: {contact_setting.value.get('address')}")
    print(f"  Current Map URL: {contact_setting.value.get('map_embed_url')[:80]}...")
    
    # Uttara 10, Dhaka coordinates: 23.8759° N, 90.3795° E
    contact_setting.value['map_latitude'] = '23.8759'
    contact_setting.value['map_longitude'] = '90.3795'
    
    # Keep the existing OpenStreetMap URL
    contact_setting.save()
    
    print(f"\n✅ Added coordinates to settings:")
    print(f"   Latitude: {contact_setting.value['map_latitude']}")
    print(f"   Longitude: {contact_setting.value['map_longitude']}")
    print("\n✨ Now you can:")
    print("   1. Edit coordinates in Dashboard > Contacts > Settings")
    print("   2. Click 'Preview Map Location' to see the location")
    print("   3. Click 'Use My Current Location' to auto-detect")
    print("   4. Map URL will auto-generate from coordinates")
else:
    print("❌ No contact settings found in database")
    print("Creating default settings...")
    
    ContactSetting.objects.create(
        key='contact_details',
        value={
            'business_name': 'Manob Bazar',
            'phone': '01777173040',
            'email': 'contact@manobbazar.com',
            'business_hours': 'Mon-Fri: 9AM-6PM',
            'address': 'Hanif Ali Mor, Uttara 10, Dhaka',
            'map_latitude': '23.8759',
            'map_longitude': '90.3795',
            'map_embed_url': 'https://www.openstreetmap.org/export/embed.html?bbox=90.3745%2C23.8709%2C90.3845%2C23.8809&layer=mapnik&marker=23.8759%2C90.3795',
            'additional_info': '',
            'social_media': {
                'facebook': 'https://www.facebook.com/ManobBazar',
                'twitter': '',
                'instagram': '',
                'linkedin': ''
            }
        },
        description='Contact page settings and business information'
    )
    print("✅ Default settings created with coordinates!")
