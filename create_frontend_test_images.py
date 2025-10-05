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

def create_test_images():
    print("=== CREATING TEST IMAGES FOR FRONTEND ===\n")
    
    # Get first product
    product = Product.objects.first()
    print(f"Using product: {product.name} (ID: {product.id})")
    
    # Create some test images using media library paths
    test_images = [
        {
            'image': '/media/products/ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
            'alt_text': 'Primary product image',
            'is_primary': True
        },
        {
            'image': '/media/products/test2.jpg',
            'alt_text': 'Secondary product image',
            'is_primary': False
        },
        {
            'image': 'products/old-format.jpg',
            'alt_text': 'Old format image',
            'is_primary': False
        }
    ]
    
    created_images = []
    
    for img_data in test_images:
        image = ProductImage.objects.create(
            product=product,
            **img_data
        )
        created_images.append(image)
        print(f"✅ Created image ID {image.id}:")
        print(f"   Image field: '{image.image}'")
        print(f"   Image URL: '{image.image_url}'")
        print(f"   Is primary: {image.is_primary}")
        print()
    
    print(f"Total images for product '{product.name}': {product.images.count()}")
    
    # Test the product serializer to see if images are included
    from dashboard.serializers import ProductDashboardSerializer
    
    serializer = ProductDashboardSerializer(product)
    print(f"\nProduct serializer output includes images: {'images' in serializer.data}")
    
    if 'images' in serializer.data:
        print(f"Number of images in serializer: {len(serializer.data['images'])}")
        for i, img in enumerate(serializer.data['images']):
            print(f"  Image {i+1}: {img.get('image_display', img.get('image'))}")
    
    return created_images

if __name__ == '__main__':
    images = create_test_images()
    
    print(f"\n✅ Created {len(images)} test images")
    print("You can now test the frontend at: http://127.0.0.1:8000/mb-admin/products/")
    print("The images should display in the product management interface.")
    
    # Optional: Don't clean up so we can test in frontend
    # Uncomment the next lines if you want to clean up:
    # for img in images:
    #     img.delete()
    # print("Cleaned up test images")