#!/usr/bin/env python
"""
Debug script to check image storage and display issues
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductImage
from django.contrib.auth import get_user_model
from django.test import Client

def debug_image_issues():
    """Debug image storage and display problems"""
    
    print("=== DEBUGGING IMAGE ISSUES ===\n")
    
    # Check existing products with images
    products_with_images = Product.objects.filter(images__isnull=False).distinct()
    print(f"Found {products_with_images.count()} products with images:")
    
    for product in products_with_images:
        print(f"\nProduct: {product.name} (ID: {product.id})")
        images = product.images.all()
        print(f"  Has {images.count()} images:")
        
        for img in images:
            print(f"    - Image field value: '{img.image}'")
            print(f"    - Image URL property: '{img.image_url}'")
            print(f"    - Alt text: '{img.alt_text}'")
            print(f"    - Is primary: {img.is_primary}")
            print()
    
    # Test creating a new image via API
    print("\n=== TESTING API IMAGE CREATION ===")
    
    client = Client()
    User = get_user_model()
    admin_user = User.objects.filter(is_superuser=True).first()
    
    if admin_user:
        client.force_login(admin_user)
        
        # Get media files
        response = client.get('/mb-admin/api/media/')
        if response.status_code == 200:
            data = response.json()
            files = data.get('files', [])
            
            if files and products_with_images.exists():
                test_product = products_with_images.first()
                test_image = files[0]
                
                print(f"Testing with product: {test_product.name}")
                print(f"Using media file: {test_image['filename']}")
                print(f"Media file URL: {test_image['url']}")
                
                # Test creating image via API
                image_data = {
                    'product': test_product.id,
                    'alt_text': f"Test image from API: {test_image['filename']}",
                    'is_primary': False,
                    'image_url': test_image['url'],
                    'filename': test_image['filename']
                }
                
                response = client.post('/mb-admin/api/product-images/', image_data)
                print(f"API response status: {response.status_code}")
                
                if response.status_code == 201:
                    print("✅ Successfully created image via API")
                    response_data = response.json()
                    print(f"Response data: {response_data}")
                    
                    # Check what was actually saved
                    new_image = ProductImage.objects.get(id=response_data['id'])
                    print(f"Saved image field: '{new_image.image}'")
                    print(f"Saved image URL: '{new_image.image_url}'")
                else:
                    print(f"❌ Failed to create image: {response.content}")
            else:
                print("No media files or products available for testing")
    
    # Test the product detail API
    print("\n=== TESTING PRODUCT DETAIL API ===")
    
    if products_with_images.exists():
        test_product = products_with_images.first()
        response = client.get(f'/mb-admin/api/products/{test_product.id}/')
        
        if response.status_code == 200:
            data = response.json()
            print(f"Product detail API response for {test_product.name}:")
            print(f"  Images count: {len(data.get('images', []))}")
            
            for img in data.get('images', []):
                print(f"    - API image field: '{img.get('image', 'NOT FOUND')}'")
                print(f"    - API image_display: '{img.get('image_display', 'NOT FOUND')}'")
                print(f"    - Alt text: '{img.get('alt_text', '')}'")
        else:
            print(f"Failed to get product detail: {response.status_code}")

if __name__ == "__main__":
    debug_image_issues()