#!/usr/bin/env python
"""
Test script to check pages API endpoints
"""
import os
import django
import requests
from django.test import Client
from django.contrib.auth import get_user_model

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def test_pages_api():
    """Test pages API endpoints"""
    client = Client()
    User = get_user_model()
    
    print("=== Testing Pages API Endpoints ===")
    
    # Create or get admin user for testing
    try:
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='testadmin',
                email='admin@example.com',
                password='testpass123'
            )
        print(f"Using admin user: {admin_user.username}")
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return
    
    # Login as admin
    client.force_login(admin_user)
    
    # Test 1: Statistics endpoint
    print("\n--- Test 1: Pages Statistics ---")
    try:
        response = client.get('/mb-admin/api/pages/pages/statistics/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error response: {response.content.decode()[:500]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Pages list endpoint
    print("\n--- Test 2: Pages List ---")
    try:
        response = client.get('/mb-admin/api/pages/pages/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Pages count: {data.get('count', 'Unknown')}")
            if 'results' in data:
                print(f"First page: {data['results'][0] if data['results'] else 'None'}")
        else:
            print(f"Error response: {response.content.decode()[:500]}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Categories endpoint  
    print("\n--- Test 3: Page Categories ---")
    try:
        response = client.get('/mb-admin/api/pages/categories/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Categories count: {data.get('count', 'Unknown')}")
        else:
            print(f"Error response: {response.content.decode()[:500]}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    test_pages_api()