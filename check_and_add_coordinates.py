"""
Check and add map coordinates to contact settings
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from contact.models import ContactSetting

# Get the contact settings
contact_setting = ContactSetting.objects.filter(key='contact_details').first()

if contact_setting:
    print("=" * 80)
    print("CURRENT CONTACT SETTINGS")
    print("=" * 80)
    print(f"Business Name: {contact_setting.value.get('business_name')}")
    print(f"Address: {contact_setting.value.get('address')}")
    print(f"Map Coordinates: {contact_setting.value.get('map_coordinates')}")
    print(f"Map Embed URL: {contact_setting.value.get('map_embed_url')}")
    print()
    
    # Add map coordinates if not exists
    if not contact_setting.value.get('map_coordinates'):
        print("Adding map coordinates for Uttara 10, Dhaka...")
        contact_setting.value['map_coordinates'] = "23.8759,90.3795"
        contact_setting.save()
        print("✅ Map coordinates added: 23.8759,90.3795")
    else:
        print(f"✅ Map coordinates already set: {contact_setting.value.get('map_coordinates')}")
    
    print()
    print("=" * 80)
    print("SATELLITE MAP SHOULD NOW DISPLAY")
    print("=" * 80)
    print("Visit: http://127.0.0.1:8000/contact/")
    print()
else:
    print("❌ No contact settings found in database")
    print("Creating new contact settings with coordinates...")
    
    ContactSetting.objects.create(
        key='contact_details',
        value={
            'business_name': 'Manob Bazar',
            'address': 'Hanif Ali Mor, Uttara 10, Dhaka',
            'phone': '01777173040',
            'email': 'contact@manobbazar.com',
            'business_hours': 'Mon-Fri: 9AM-6PM',
            'map_coordinates': '23.8759,90.3795',
            'map_embed_url': '',
            'social_media': {
                'facebook': 'https://www.facebook.com/ManobBazar',
                'twitter': '',
                'instagram': '',
                'linkedin': ''
            }
        },
        description='Contact page settings'
    )
    print("✅ Contact settings created with map coordinates")
