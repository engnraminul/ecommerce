#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth import get_user_model

def test_cart_endpoints():
    """Test all cart-related endpoints"""
    client = Client()
    
    print("=== CART API ENDPOINT TESTS ===\n")
    
    # Test 1: Basic cart endpoint
    response = client.get('/api/v1/cart/')
    print(f"✓ GET /api/v1/cart/ - Status: {response.status_code}")
    
    # Test 2: Cart with location parameter (should still work)
    response = client.get('/api/v1/cart/?location=dhaka')
    print(f"✓ GET /api/v1/cart/?location=dhaka - Status: {response.status_code}")
    
    # Test 3: Cart summary
    response = client.get('/api/v1/cart/summary/')
    print(f"✓ GET /api/v1/cart/summary/ - Status: {response.status_code}")
    
    # Test 4: Shipping options
    response = client.get('/api/v1/cart/shipping-options/?location=dhaka')
    print(f"✓ GET /api/v1/cart/shipping-options/?location=dhaka - Status: {response.status_code}")
    
    # Test 5: Test with authenticated user
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if admin_user:
        client.force_login(admin_user)
        response = client.get('/api/v1/cart/')
        print(f"✓ GET /api/v1/cart/ (authenticated) - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"  - Cart items: {len(data.get('items', []))}")
            print(f"  - Total amount: {data.get('total_amount', 'N/A')}")
    
    print("\n=== PRODUCT IMAGE TESTS ===\n")
    
    # Test product endpoints for image handling
    response = client.get('/api/v1/products/')
    print(f"✓ GET /api/v1/products/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        products_data = response.json()
        if products_data.get('results'):
            first_product = products_data['results'][0]
            print(f"  - First product: {first_product.get('name', 'N/A')}")
            print(f"  - Primary image: {first_product.get('primary_image', 'None')}")
    
    print("\n=== All tests completed ===")

if __name__ == "__main__":
    test_cart_endpoints()