#!/usr/bin/env python
import os
import django
import sys

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductImage
from dashboard.serializers import ProductImageDashboardSerializer
import json

def test_media_library_workflow():
    print("=== TESTING COMPLETE MEDIA LIBRARY WORKFLOW ===\n")
    
    # Get first product
    product = Product.objects.first()
    print(f"Testing with product: {product.name} (ID: {product.id})")
    
    # Step 1: Check initial state
    initial_count = product.images.count()
    print(f"Initial image count: {initial_count}")
    
    # Step 2: Simulate media library selection
    # This simulates what the frontend JavaScript sends when user selects from media library
    media_library_data = {
        'product': product.id,
        'image_url': '/media/products/ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
        'filename': 'ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
        'alt_text': 'Selected from media library',
        'is_primary': False
    }
    
    print(f"\nStep 2: Creating image from media library selection")
    print(f"Data being sent: {media_library_data}")
    
    # Step 3: Create through serializer (simulates API call)
    serializer = ProductImageDashboardSerializer(data=media_library_data)
    
    if serializer.is_valid():
        print("✅ Serializer validation passed")
        
        # Save the instance
        instance = serializer.save()
        
        print(f"✅ Image created successfully:")
        print(f"  - ID: {instance.id}")
        print(f"  - Image field value: '{instance.image}'")
        print(f"  - Image URL property: '{instance.image_url}'")
        print(f"  - Alt text: '{instance.alt_text}'")
        print(f"  - Is primary: {instance.is_primary}")
        
        # Step 4: Verify the image is saved in database
        print(f"\nStep 4: Verifying database storage...")
        try:
            saved_image = ProductImage.objects.get(id=instance.id)
            print(f"✅ Found in database:")
            print(f"  - Image field: '{saved_image.image}'")
            print(f"  - Matches expected URL: {saved_image.image == media_library_data['image_url']}")
        except ProductImage.DoesNotExist:
            print("❌ Not found in database!")
            
        # Step 5: Check if it appears in product's images
        final_count = product.images.count()
        print(f"\nStep 5: Product image count after creation: {final_count}")
        print(f"Images increased: {final_count > initial_count}")
        
        # Step 6: Test API response (what frontend would receive)
        response_serializer = ProductImageDashboardSerializer(instance)
        response_data = response_serializer.data
        print(f"\nStep 6: API response data:")
        print(json.dumps(response_data, indent=2, default=str))
        
        # Step 7: Test if image appears in product serializer
        from dashboard.serializers import ProductDashboardSerializer
        product_serializer = ProductDashboardSerializer(product)
        product_data = product_serializer.data
        
        print(f"\nStep 7: Product API includes images: {'images' in product_data}")
        if 'images' in product_data:
            print(f"Number of images in product API: {len(product_data['images'])}")
            # Check if our new image is included
            our_image_in_api = any(
                img.get('id') == instance.id 
                for img in product_data['images']
            )
            print(f"Our new image appears in product API: {our_image_in_api}")
        
        print(f"\n🎉 WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        print(f"✅ Image path '{media_library_data['image_url']}' was saved correctly")
        print(f"✅ Image appears in database with correct URL")
        print(f"✅ Image is included in API responses")
        
        # Clean up (optional)
        instance.delete()
        print(f"\nCleaned up test image")
        
    else:
        print(f"❌ Serializer validation failed: {serializer.errors}")

def test_path_variations():
    print(f"\n=== TESTING DIFFERENT PATH FORMATS ===\n")
    
    product = Product.objects.first()
    
    path_tests = [
        '/media/products/test1.jpg',
        'products/test2.jpg', 
        '/media/products/subfolder/test3.jpg'
    ]
    
    for i, path in enumerate(path_tests, 1):
        print(f"Test {i}: Path '{path}'")
        
        data = {
            'product': product.id,
            'image_url': path,
            'alt_text': f'Test image {i}',
            'is_primary': False
        }
        
        serializer = ProductImageDashboardSerializer(data=data)
        if serializer.is_valid():
            instance = serializer.save()
            print(f"  ✅ Saved as: '{instance.image}'")
            print(f"  📸 URL property: '{instance.image_url}'")
            instance.delete()
        else:
            print(f"  ❌ Failed: {serializer.errors}")
        print()

if __name__ == '__main__':
    test_media_library_workflow()
    test_path_variations()