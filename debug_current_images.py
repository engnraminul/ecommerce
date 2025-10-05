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

def check_current_images():
    print("=== CHECKING CURRENT PRODUCT IMAGES ===\n")
    
    # Get product with images
    product = Product.objects.filter(images__isnull=False).first()
    if not product:
        print("No products with images found!")
        return
    
    print(f"Product: {product.name} (ID: {product.id})")
    
    images = ProductImage.objects.filter(product=product)
    print(f"Found {images.count()} images:\n")
    
    for i, image in enumerate(images, 1):
        print(f"Image {i}:")
        print(f"  - ID: {image.id}")
        print(f"  - Image field: '{image.image}'")
        print(f"  - Image URL property: '{image.image_url}'")
        print(f"  - Alt text: '{image.alt_text}'")
        print(f"  - Is primary: {image.is_primary}")
        print(f"  - Created: {image.created_at}")
        print()
    
    # Test creating a new image directly through model
    print("=== TESTING DIRECT MODEL CREATION ===")
    
    test_image = ProductImage.objects.create(
        product=product,
        image='/media/products/ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
        alt_text='Direct model test',
        is_primary=False
    )
    
    print(f"Created image via model:")
    print(f"  - ID: {test_image.id}")
    print(f"  - Image field: '{test_image.image}'")
    print(f"  - Image URL property: '{test_image.image_url}'")
    
    # Clean up test image
    test_image.delete()
    print("Cleaned up test image")

if __name__ == '__main__':
    check_current_images()