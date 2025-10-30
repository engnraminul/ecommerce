#!/usr/bin/env python
"""
Test script to verify user edit API fix
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

def test_user_update_api():
    """Test user update API with dashboard permissions"""
    print("=== Testing User Update API ===")
    
    # Get a test user to update
    try:
        user = User.objects.get(email='phonekobra@gmail.com')
        print(f"Testing with user: {user.email}")
        
        # Create a Django test client
        client = Client()
        
        # Login as superuser first
        superuser = User.objects.filter(is_superuser=True).first()
        if superuser:
            client.force_login(superuser)
            print(f"Logged in as: {superuser.email}")
        
        # Prepare update data (simulate what the frontend sends)
        update_data = {
            'username': user.username,  # Include username
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone': user.phone or '',
            'is_active': user.is_active,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'dashboard_permissions': {
                'allowed_tabs': ['home', 'products', 'orders']  # Test with limited permissions
            }
        }
        
        print(f"Sending update data: {json.dumps(update_data, indent=2)}")
        
        # Make the API call
        response = client.put(
            f'/mb-admin/api/users/{user.id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        if response.status_code == 200:
            print("✅ User update successful!")
            
            # Verify the permissions were updated
            user.refresh_from_db()
            try:
                perm = DashboardPermission.objects.get(user=user)
                print(f"Updated permissions: {perm.allowed_tabs}")
                
                if set(perm.allowed_tabs) == set(['home', 'products', 'orders']):
                    print("✅ Permissions updated correctly!")
                    return True
                else:
                    print(f"✗ Permissions not updated correctly. Expected: ['home', 'products', 'orders'], Got: {perm.allowed_tabs}")
                    return False
                    
            except DashboardPermission.DoesNotExist:
                print("✗ No permission object found after update")
                return False
        else:
            print(f"✗ User update failed: {response.content.decode()}")
            return False
            
    except User.DoesNotExist:
        print("Test user not found")
        return False
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def test_create_user_api():
    """Test user creation API with dashboard permissions"""
    print("\n=== Testing User Creation API ===")
    
    # Create a Django test client
    client = Client()
    
    # Login as superuser
    superuser = User.objects.filter(is_superuser=True).first()
    if superuser:
        client.force_login(superuser)
    
    # Prepare creation data
    create_data = {
        'username': 'testuser_api',
        'email': 'testuser_api@example.com',
        'first_name': 'Test',
        'last_name': 'User',
        'password': 'testpassword123',
        'is_active': True,
        'is_staff': False,
        'is_superuser': False,
        'dashboard_permissions': {
            'allowed_tabs': ['home', 'products']
        }
    }
    
    print(f"Creating user with data: {json.dumps(create_data, indent=2)}")
    
    # Make the API call
    response = client.post(
        '/mb-admin/api/users/',
        data=json.dumps(create_data),
        content_type='application/json'
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response content: {response.content.decode()}")
    
    if response.status_code == 201:
        print("✅ User creation successful!")
        
        # Clean up - delete the test user
        try:
            test_user = User.objects.get(email='testuser_api@example.com')
            test_user.delete()
            print("✅ Test user cleaned up")
        except User.DoesNotExist:
            pass
        
        return True
    else:
        print(f"✗ User creation failed: {response.content.decode()}")
        return False

def main():
    """Run all tests"""
    print("User Edit API Fix - Verification Tests")
    print("=" * 50)
    
    update_success = test_user_update_api()
    create_success = test_create_user_api()
    
    print("\n" + "=" * 50)
    if update_success and create_success:
        print("✅ ALL API TESTS PASSED!")
        print("✅ User edit functionality is working correctly")
        print("✅ Dashboard permissions API is operational")
    else:
        print("❌ Some API tests failed")
        
        if not update_success:
            print("- User update API needs fixing")
        if not create_success:
            print("- User creation API needs fixing")

if __name__ == "__main__":
    main()