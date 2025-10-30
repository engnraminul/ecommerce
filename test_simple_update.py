#!/usr/bin/env python
"""
Simple test for user update API
"""

import os
import django
import json

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from users.models import DashboardPermission

User = get_user_model()

def test_simple_update():
    """Test simple user update"""
    print("=== Testing Simple User Update ===")
    
    try:
        user = User.objects.get(email='phonekobra@gmail.com')
        print(f"Testing with user: {user.email}")
        
        # Create a Django test client
        client = Client()
        
        # Login as superuser
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            client.force_login(superuser)
        
        # Simple update without dashboard permissions first
        update_data = {
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone or '',
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        
        print("Testing update without dashboard permissions...")
        response = client.put(
            f'/mb-admin/api/users/{user.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.content.decode()}")
            return False
        
        print("✅ Simple update works!")
        
        # Now test with dashboard permissions
        update_data['dashboard_permissions'] = {
            'allowed_tabs': ['home', 'products', 'orders']
        }
        
        print("Testing update with dashboard permissions...")
        response = client.put(
            f'/mb-admin/api/users/{user.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.content.decode()}")
            return False
        
        print("✅ Update with dashboard permissions works!")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_simple_update()