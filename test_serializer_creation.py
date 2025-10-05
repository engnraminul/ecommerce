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

def test_serializer_creation():
    print("=== TESTING PRODUCTIMAGE SERIALIZER ===\n")
    
    # Get first product
    product = Product.objects.first()
    print(f"Using product: {product.name} (ID: {product.id})")
    
    # Test data like what would come from frontend
    test_data = {
        'product': product.id,
        'image_url': '/media/products/test-from-library.jpg',
        'filename': 'test-from-library.jpg',
        'alt_text': 'Test from serializer',
        'is_primary': False
    }
    
    print(f"Test data: {test_data}")
    
    # Create through serializer
    serializer = ProductImageDashboardSerializer(data=test_data)
    
    if serializer.is_valid():
        print("✅ Serializer validation passed")
        
        # Save the instance
        instance = serializer.save()
        
        print(f"✅ Instance created:")
        print(f"  - ID: {instance.id}")
        print(f"  - Image field: '{instance.image}'")
        print(f"  - Image URL property: '{instance.image_url}'")
        print(f"  - Alt text: '{instance.alt_text}'")
        print(f"  - Is primary: {instance.is_primary}")
        
        # Test serializer output
        output_serializer = ProductImageDashboardSerializer(instance)
        print(f"\nSerialized output: {output_serializer.data}")
        
        # Clean up
        instance.delete()
        print("\nCleaned up test image")
        
    else:
        print(f"❌ Serializer validation failed: {serializer.errors}")

def test_different_url_formats():
    print("\n=== TESTING DIFFERENT URL FORMATS ===\n")
    
    product = Product.objects.first()
    
    test_cases = [
        {
            'name': 'Full media URL',
            'data': {
                'product': product.id,
                'image_url': '/media/products/full-url-test.jpg',
                'alt_text': 'Full URL test',
                'is_primary': False
            }
        },
        {
            'name': 'Relative path',
            'data': {
                'product': product.id,
                'image_url': 'products/relative-path-test.jpg',
                'alt_text': 'Relative path test',
                'is_primary': False
            }
        },
        {
            'name': 'HTTP URL',
            'data': {
                'product': product.id,
                'image_url': 'https://example.com/test.jpg',
                'alt_text': 'HTTP URL test',
                'is_primary': False
            }
        }
    ]
    
    created_instances = []
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        serializer = ProductImageDashboardSerializer(data=test_case['data'])
        
        if serializer.is_valid():
            instance = serializer.save()
            created_instances.append(instance)
            
            print(f"  ✅ Created: ID {instance.id}")
            print(f"     Image field: '{instance.image}'")
            print(f"     Image URL: '{instance.image_url}'")
        else:
            print(f"  ❌ Failed: {serializer.errors}")
        print()
    
    # Clean up
    for instance in created_instances:
        instance.delete()
    print(f"Cleaned up {len(created_instances)} test images")

if __name__ == '__main__':
    test_serializer_creation()
    test_different_url_formats()