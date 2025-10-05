#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

# Create a test client and login as admin
client = Client()

try:
    admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()
    client.force_login(admin_user)
    
    print("=== Debugging Media API ===")
    
    # Test different parameters
    test_urls = [
        '/mb-admin/api/media/',
        '/mb-admin/api/media/?type=all',
        '/mb-admin/api/media/?type=images',
        '/mb-admin/api/media/?page=1&per_page=12',
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        response = client.get(url)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"Files count: {len(data.get('files', []))}")
            print(f"Total: {data.get('total')}")
            
            if data.get('files'):
                first_file = data['files'][0]
                print(f"First file: {first_file.get('filename')} - {first_file.get('url')}")
        else:
            print(f"Error: {response.content.decode()}")
    
    # Also test the media directories directly
    print(f"\n=== Direct Directory Check ===")
    media_dirs = ['products', 'variants', 'reviews']
    
    for media_dir in media_dirs:
        dir_path = os.path.join(settings.MEDIA_ROOT, media_dir)
        if os.path.exists(dir_path):
            files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
            print(f"{media_dir}: {len(files)} files")
            if files:
                print(f"  Sample: {files[0]}")
        else:
            print(f"{media_dir}: Directory not found")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()