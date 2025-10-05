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

def test_edit_workflow():
    print("=== TESTING EDIT WORKFLOW ===\n")
    
    # Get first product
    product = Product.objects.first()
    print(f"Testing with product: {product.name} (ID: {product.id})")
    
    # Check current images
    current_images = product.images.all()
    print(f"Current images: {current_images.count()}")
    for img in current_images:
        print(f"  - ID: {img.id}, Image: '{img.image}', Primary: {img.is_primary}")
    
    # Test adding a new image via API (simulating what edit form does)
    print(f"\nTesting adding new image via edit form workflow...")
    
    test_data = {
        'product': product.id,
        'image_url': '/media/products/edit-test.jpg',
        'filename': 'edit-test.jpg',
        'alt_text': 'Added from edit form',
        'is_primary': False
    }
    
    print(f"Sending data: {test_data}")
    
    serializer = ProductImageDashboardSerializer(data=test_data)
    if serializer.is_valid():
        instance = serializer.save()
        print(f"✅ Successfully created:")
        print(f"  - ID: {instance.id}")
        print(f"  - Image field: '{instance.image}'")
        print(f"  - Image URL: '{instance.image_url}'")
        print(f"  - Alt text: '{instance.alt_text}'")
        
        # Verify it appears in product
        updated_count = product.images.count()
        print(f"\nProduct image count after: {updated_count}")
        
        # Test product serializer response
        from dashboard.serializers import ProductDashboardSerializer
        product_serializer = ProductDashboardSerializer(product)
        images_in_api = product_serializer.data.get('images', [])
        print(f"Images in product API: {len(images_in_api)}")
        
        # Check if our new image is there
        our_image = next((img for img in images_in_api if img['id'] == instance.id), None)
        if our_image:
            print(f"✅ New image found in product API:")
            print(f"  - Image display: '{our_image.get('image_display')}'")
        else:
            print(f"❌ New image NOT found in product API")
        
        # Clean up
        instance.delete()
        print(f"\nCleaned up test image")
        
    else:
        print(f"❌ Validation failed: {serializer.errors}")

def check_frontend_workflow():
    print(f"\n=== CHECKING FRONTEND DATA FLOW ===\n")
    
    # This simulates exactly what the frontend JavaScript should send
    # when user selects from media library in edit form
    
    product = Product.objects.first()
    
    # This is what the JavaScript createImagePreviewCard stores in dataset.mediaFile
    media_file_data = {
        "url": "/media/products/ddcdbdbfad81445fa4618deb9ae52ed0.jpg",
        "filename": "ddcdbdbfad81445fa4618deb9ae52ed0.jpg",
        "size_formatted": "45.2 KB",
        "is_image": True
    }
    
    # This is what the JavaScript updateProduct function should extract and send
    image_data = {
        "media_file": media_file_data,
        "alt_text": "Test from frontend workflow",
        "is_primary": False,
        "is_from_library": True
    }
    
    print(f"Frontend would send this to uploadProductImages:")
    print(json.dumps(image_data, indent=2))
    
    # This is what uploadProductImages should send to API
    api_data = {
        'product': product.id,
        'image_url': image_data['media_file']['url'],
        'filename': image_data['media_file']['filename'],
        'alt_text': image_data['alt_text'],
        'is_primary': image_data['is_primary']
    }
    
    print(f"\nAPI should receive:")
    print(json.dumps(api_data, indent=2))
    
    # Test this flow
    serializer = ProductImageDashboardSerializer(data=api_data)
    if serializer.is_valid():
        instance = serializer.save()
        print(f"\n✅ Frontend workflow would succeed:")
        print(f"  - Image saved as: '{instance.image}'")
        print(f"  - Matches expected: {instance.image == api_data['image_url']}")
        
        # Clean up
        instance.delete()
        print(f"Cleaned up test")
    else:
        print(f"\n❌ Frontend workflow would fail: {serializer.errors}")

if __name__ == '__main__':
    test_edit_workflow()
    check_frontend_workflow()