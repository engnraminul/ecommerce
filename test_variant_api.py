#!/usr/bin/env python
import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductVariant
from dashboard.serializers import ProductVariantDashboardSerializer

# Find first product with variants
product = Product.objects.filter(variants__isnull=False).first()
if product:
    print(f"Testing with product: {product.name}")
    
    # Get first variant
    variant = product.variants.first()
    if variant:
        print(f"Found variant: {variant.name}")
        print(f"Current image: {variant.image}")
        print(f"Current image_url: {variant.image_url}")
        
        # Test serializer output
        serializer = ProductVariantDashboardSerializer(variant)
        print("\nDashboard Serializer Output:")
        print(json.dumps(serializer.data, indent=2, default=str))
        
        # Test the API endpoint simulation
        from django.test.client import Client
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if admin_user:
            client = Client()
            client.force_login(admin_user)
            
            # Test GET variant details
            response = client.get(f'/mb-admin/api/variants/{variant.id}/')
            print(f"\nAPI GET Response Status: {response.status_code}")
            if response.status_code == 200:
                print("API Response Data:")
                print(json.dumps(response.json(), indent=2, default=str))
            else:
                print(f"API Response: {response.content}")
                
            # Test updating variant with media library URL
            test_url = "/media/test-image.jpg"
            update_data = {
                'name': variant.name,
                'price': variant.price,
                'product': variant.product.id,
                'is_active': variant.is_active,
                'image_url_input': test_url,
            }
            
            print(f"\nTesting update with media library URL: {test_url}")
            response = client.put(
                f'/mb-admin/api/variants/{variant.id}/',
                data=update_data,
                content_type='multipart/form-data'
            )
            print(f"Update Response Status: {response.status_code}")
            if response.status_code != 200:
                print(f"Update Response: {response.content}")
            else:
                print("Update Response Data:")
                print(json.dumps(response.json(), indent=2, default=str))
                
                # Reload variant and check image
                variant.refresh_from_db()
                print(f"\nAfter update:")
                print(f"Variant image: {variant.image}")
                print(f"Variant image_url: {variant.image_url}")
        else:
            print("No admin user found for API testing")
    else:
        print("No variants found for this product")
else:
    print("No products with variants found")