#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from products.models import Product, ProductImage

User = get_user_model()

def test_complete_workflow():
    # Create a test client and login as admin
    client = Client()
    
    try:
        admin_user = User.objects.filter(is_staff=True, is_superuser=True).first()
        client.force_login(admin_user)
        
        print("=== Testing Complete Media Library to Product Workflow ===")
        
        # Get a product to test with
        product = Product.objects.first()
        print(f"Testing with product: {product.name} (ID: {product.id})")
        
        # Count initial images
        initial_count = ProductImage.objects.filter(product=product).count()
        print(f"Initial image count: {initial_count}")
        
        # Test creating an image via API (simulating media library selection)
        print("\n1. Testing image creation via API...")
        test_data = {
            'product': product.id,
            'image_url_input': '/media/products/ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
            'alt_text': 'Test from media library',
            'is_primary': 'false'
        }
        
        response = client.post('/mb-admin/api/product-images/', test_data)
        print(f"Create Status: {response.status_code}")
        
        if response.status_code == 201:
            created_image = response.json()
            print(f"Created image ID: {created_image['id']}")
            print(f"Image URL: {created_image.get('image_url')}")
            
            # Verify the image was created
            new_count = ProductImage.objects.filter(product=product).count()
            print(f"New image count: {new_count}")
            
            # Test fetching product images
            print("\n2. Testing product images retrieval...")
            response = client.get(f'/mb-admin/api/product-images/?product={product.id}')
            print(f"Fetch Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                images = data.get('results', [])
                print(f"Fetched {len(images)} images")
                
                for img in images:
                    print(f"  - ID: {img['id']}, URL: {img.get('image_url', img.get('image'))}, Primary: {img['is_primary']}")
                
                # Test toggle primary image
                print("\n3. Testing primary image toggle...")
                if images:
                    test_image_id = created_image['id']
                    toggle_data = {'is_primary': True}
                    
                    response = client.patch(f'/mb-admin/api/product-images/{test_image_id}/', 
                                         toggle_data, content_type='application/json')
                    print(f"Toggle Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("Primary toggle successful")
                        
                        # Verify only one primary image
                        primary_images = ProductImage.objects.filter(product=product, is_primary=True)
                        print(f"Primary images count: {primary_images.count()}")
                        
                # Test delete image
                print("\n4. Testing image deletion...")
                response = client.delete(f'/mb-admin/api/product-images/{created_image["id"]}/')
                print(f"Delete Status: {response.status_code}")
                
                if response.status_code == 204:
                    final_count = ProductImage.objects.filter(product=product).count()
                    print(f"Final image count: {final_count}")
                    print("Image deleted successfully")
                
        else:
            print(f"Error: {response.content.decode()}")
        
        print("\n=== Workflow Test Complete ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_workflow()