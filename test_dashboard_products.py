#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth import get_user_model

def test_dashboard_products_api():
    """Test the dashboard products API endpoint"""
    client = Client()
    
    print("=== DASHBOARD PRODUCTS API TESTS ===\n")
    
    # Test without authentication first
    try:
        response = client.get('/mb-admin/api/products/')
        print(f"GET /mb-admin/api/products/ (unauthenticated) - Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.content.decode()[:500]}")
    except Exception as e:
        print(f"Exception testing unauthenticated: {e}")
    
    # Test with authentication
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if admin_user:
        client.force_login(admin_user)
        try:
            response = client.get('/mb-admin/api/products/')
            print(f"GET /mb-admin/api/products/ (authenticated) - Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error Response: {response.content.decode()[:1000]}")
            else:
                data = response.json()
                print(f"Success - Found {len(data.get('results', []))} products")
                
                # Check if any product data is problematic
                if data.get('results'):
                    first_product = data['results'][0]
                    print(f"First Product: {first_product.get('name', 'N/A')}")
                    print(f"Product ID: {first_product.get('id', 'N/A')}")
                    print(f"Primary Image: {first_product.get('primary_image', 'None')}")
                    
        except Exception as e:
            print(f"Exception testing authenticated dashboard API: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("No admin user found for authentication test")
        
    # Test with pagination parameter
    if admin_user:
        try:
            response = client.get('/mb-admin/api/products/?page=1')
            print(f"GET /mb-admin/api/products/?page=1 - Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error Response: {response.content.decode()[:500]}")
                
        except Exception as e:
            print(f"Exception testing paginated API: {e}")

if __name__ == "__main__":
    test_dashboard_products_api()