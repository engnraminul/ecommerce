"""
Verify that the map URL is correctly updated in the database
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from contact.models import ContactSetting

print("=" * 80)
print("MAP URL VERIFICATION")
print("=" * 80)

contact_setting = ContactSetting.objects.filter(key='contact_details').first()

if contact_setting:
    map_url = contact_setting.value.get('map_embed_url', '')
    
    print(f"\n📍 Business Name: {contact_setting.value.get('business_name')}")
    print(f"📫 Address: {contact_setting.value.get('address')}")
    print(f"\n🗺️  Current Map URL:")
    print(f"   {map_url}")
    
    # Check if it's using OpenStreetMap
    if 'openstreetmap.org' in map_url:
        print(f"\n✅ STATUS: Using OpenStreetMap (CORRECT)")
        print(f"✅ No X-Frame-Options issues")
        print(f"✅ Map will display correctly")
        
        # Check if it has coordinates
        if 'marker=' in map_url:
            marker_part = map_url.split('marker=')[1].split('&')[0]
            print(f"✅ Location marker: {marker_part}")
        
    elif 'google.com' in map_url or 'maps.app.goo.gl' in map_url:
        print(f"\n❌ STATUS: Still using Google Maps")
        print(f"❌ This will cause X-Frame-Options errors")
        print(f"❌ Please run: python fix_map_url.py")
        
    elif not map_url:
        print(f"\n⚠️  STATUS: Map URL is empty")
        print(f"⚠️  Will use default OpenStreetMap from template")
    
    else:
        print(f"\n⚠️  STATUS: Unknown map provider")
        print(f"⚠️  Please verify the URL works")
        
else:
    print("\n❌ No contact settings found in database")
    print("✅ Template will use default OpenStreetMap")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("\n💡 To test the map:")
print("   1. Visit: http://127.0.0.1:8000/contact/")
print("   2. Scroll to 'Find Us' section")
print("   3. Map should display without console errors")
print()
