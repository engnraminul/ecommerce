#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
import json

def test_media_delete():
    """Test the media delete functionality"""
    print("Testing Media Delete Functionality")
    print("=" * 40)
    
    # Get admin user
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("❌ No admin user found")
        return
    
    client = Client()
    client.force_login(user)
    
    # Test 1: List media files
    print("\n1. Testing media files listing...")
    response = client.get('/mb-admin/api/media/')
    print(f"Media API status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Media API failed: {response.content}")
        return
    
    media_data = response.json()
    if not media_data.get('success'):
        print(f"❌ Media API returned error: {media_data}")
        return
    
    files = media_data.get('files', [])
    print(f"✅ Found {len(files)} media files")
    
    if len(files) == 0:
        print("ℹ️ No media files found to test deletion")
        return
    
    # Test 2: Try to delete the first file
    test_file = files[0]
    file_id = test_file['id']
    filename = test_file['filename']
    
    print(f"\n2. Testing delete for file: {filename} (ID: {file_id})")
    
    # Test delete endpoint
    response = client.delete(f'/mb-admin/api/media/{file_id}/delete/')
    print(f"Delete API status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ Delete API returned success: {result.get('message')}")
        else:
            print(f"❌ Delete API returned error: {result.get('message')}")
    else:
        print(f"❌ Delete API failed with status {response.status_code}")
        print(f"Response: {response.content}")
    
    # Test 3: Check if file still exists in filesystem
    import os
    from django.conf import settings
    
    # Parse file ID to get directory and filename
    parts = file_id.split('_', 1)
    if len(parts) == 2:
        directory, filename_from_id = parts
        file_path = os.path.join(settings.MEDIA_ROOT, directory, filename_from_id)
        
        print(f"\n3. Checking filesystem for file: {file_path}")
        if os.path.exists(file_path):
            print(f"⚠️ File still exists in filesystem")
        else:
            print(f"✅ File was removed from filesystem")
    else:
        print(f"❌ Invalid file ID format: {file_id}")

if __name__ == '__main__':
    test_media_delete()