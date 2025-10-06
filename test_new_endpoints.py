#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant

User = get_user_model()

def test_new_variant_endpoints():
    print("Testing new variant endpoints...")
    
    # Get or create admin user
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
        print("Created admin user")
    
    # Create test client and login
    client = Client()
    client.force_login(user)
    
    # Get first product with variants
    product = Product.objects.filter(variants__isnull=False).first()
    if not product:
        print("No products with variants found")
        return
    
    product_id = product.id
    print(f"Testing with product: {product.name} (ID: {product_id})")
    
    # Test the new /products/{id}/variants/ endpoint
    print(f"\n1. Testing /mb-admin/api/products/{product_id}/variants/")
    response = client.get(f'/mb-admin/api/products/{product_id}/variants/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        variants = response.json()
        print(f"✅ SUCCESS: Found {len(variants)} variants")
        for i, variant in enumerate(variants[:3]):  # Show first 3
            print(f"  {i+1}. {variant['name']} (ID: {variant['id']}, Stock: {variant['stock_quantity']})")
    else:
        print(f"❌ ERROR: {response.status_code}")
        print(f"Response: {response.content.decode()}")
    
    # Test individual variant endpoint
    variant = product.variants.first()
    if variant:
        print(f"\n2. Testing /mb-admin/api/variants/{variant.id}/")
        response = client.get(f'/mb-admin/api/variants/{variant.id}/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            variant_data = response.json()
            print(f"✅ SUCCESS: Got variant details for {variant_data['name']}")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.content.decode()}")

if __name__ == '__main__':
    test_new_variant_endpoints()