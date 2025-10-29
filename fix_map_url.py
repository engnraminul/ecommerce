"""
Fix Google Maps URL in database to use OpenStreetMap embed URL
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
    print(f"  Old Map URL: {contact_setting.value.get('map_embed_url')}")
    
    # Uttara 10, Dhaka coordinates: approximately 23.8759° N, 90.3795° E
    # Create OpenStreetMap embed URL for this location
    openstreetmap_url = "https://www.openstreetmap.org/export/embed.html?bbox=90.3745%2C23.8709%2C90.3845%2C23.8809&layer=mapnik&marker=23.8759%2C90.3795"
    
    # Update the map_embed_url
    contact_setting.value['map_embed_url'] = openstreetmap_url
    contact_setting.save()
    
    print(f"\n✅ Updated Map URL to: {openstreetmap_url}")
    print("\nThis OpenStreetMap embed will work without X-Frame-Options issues!")
else:
    print("❌ No contact settings found in database")
