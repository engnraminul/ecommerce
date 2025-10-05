#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth import get_user_model

def test_products_api():
    """Test the products API to identify the 500 error"""
    client = Client()
    
    print("=== PRODUCTS API TESTS ===\n")
    
    try:
        # Test 1: Products list endpoint
        response = client.get('/api/v1/products/')
        print(f"GET /api/v1/products/ - Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response Content: {response.content.decode()[:1000]}")
        else:
            data = response.json()
            print(f"Success - Found {len(data.get('results', []))} products")
            
            # Check first product details
            if data.get('results'):
                first_product = data['results'][0]
                print(f"First Product: {first_product.get('name', 'N/A')}")
                print(f"Primary Image: {first_product.get('primary_image', 'None')}")
                print(f"Variants: {len(first_product.get('variants', []))}")
    except Exception as e:
        print(f"Exception testing products API: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test 2: Individual product detail
        response = client.get('/api/v1/products/1/')
        print(f"\nGET /api/v1/products/1/ - Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response Content: {response.content.decode()[:1000]}")
    except Exception as e:
        print(f"Exception testing product detail: {e}")
    
    # Test 3: Check if there are any broken product images
    print("\n=== CHECKING PRODUCT IMAGES ===")
    from products.models import Product, ProductImage
    
    products_with_images = Product.objects.filter(images__isnull=False).distinct()
    print(f"Products with images: {products_with_images.count()}")
    
    for product in products_with_images[:3]:
        print(f"\nProduct: {product.name}")
        for img in product.images.all():
            print(f"  Image: {img.image}")
            print(f"  Image URL: {img.image_url}")
            print(f"  Is Primary: {img.is_primary}")

if __name__ == "__main__":
    test_products_api()