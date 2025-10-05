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

def check_everything():
    print("=== CHECKING ALL DATA ===\n")
    
    # Check all products
    products = Product.objects.all()
    print(f"Total products: {products.count()}")
    
    # Check all product images
    images = ProductImage.objects.all()
    print(f"Total product images: {images.count()}")
    
    if images.exists():
        print("\nAll ProductImage records:")
        for img in images:
            print(f"  - ID: {img.id}, Product: {img.product.name}, Image: '{img.image}', Primary: {img.is_primary}")
    else:
        print("No ProductImage records found!")
    
    # Test creating one
    if products.exists():
        product = products.first()
        print(f"\nTesting with product: {product.name}")
        
        # Create test image
        test_image = ProductImage.objects.create(
            product=product,
            image='/media/products/test.jpg',
            alt_text='Test image',
            is_primary=False
        )
        
        print(f"Created test image:")
        print(f"  - ID: {test_image.id}")
        print(f"  - Image field: '{test_image.image}'")
        print(f"  - Image URL property: '{test_image.image_url}'")
        
        # Check if product now has images
        print(f"\nProduct.images.count(): {product.images.count()}")
        
        # Clean up
        test_image.delete()
        print("Cleaned up test image")

if __name__ == '__main__':
    check_everything()