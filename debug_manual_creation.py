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

def test_manual_creation():
    print("=== TESTING MANUAL PRODUCTIMAGE CREATION ===\n")
    
    # Get first product
    product = Product.objects.first()
    print(f"Using product: {product.name} (ID: {product.id})")
    
    # Try creating without using the save() method first
    print("Creating ProductImage instance...")
    test_image = ProductImage(
        product=product,
        image='/media/products/test.jpg',
        alt_text='Test image',
        is_primary=False
    )
    
    print("Instance created, now calling save()...")
    try:
        test_image.save()
        print(f"✅ Successfully saved! ID: {test_image.id}")
        
        # Verify it's in database
        saved_image = ProductImage.objects.get(id=test_image.id)
        print(f"Verified in database:")
        print(f"  - Image field: '{saved_image.image}'")
        print(f"  - Image URL: '{saved_image.image_url}'")
        
        # Clean up
        saved_image.delete()
        print("Cleaned up")
        
    except Exception as e:
        print(f"❌ Error during save: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_manual_creation()