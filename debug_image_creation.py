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
import requests
import json

def test_image_creation():
    print("=== TESTING IMAGE CREATION PROCESS ===\n")
    
    # Get first product
    product = Product.objects.first()
    if not product:
        print("No products found!")
        return
    
    print(f"Testing with product: {product.name} (ID: {product.id})")
    
    # Test creating image via API with media library URL
    url = 'http://127.0.0.1:8000/mb-admin/api/product-images/'
    
    # Test data similar to what frontend sends
    test_data = {
        'product': product.id,
        'image_url': '/media/products/ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
        'filename': 'ddcdbdbfad81445fa4618deb9ae52ed0.jpg',
        'alt_text': 'Test from debug script',
        'is_primary': False
    }
    
    print(f"Sending data: {test_data}")
    
    try:
        # Get CSRF token first
        session = requests.Session()
        csrf_response = session.get('http://127.0.0.1:8000/mb-admin/products/')
        
        # Extract CSRF token from cookies
        csrf_token = None
        for cookie in session.cookies:
            if cookie.name == 'csrftoken':
                csrf_token = cookie.value
                break
        
        if not csrf_token:
            print("Could not get CSRF token")
            return
        
        headers = {
            'X-CSRFToken': csrf_token,
            'Referer': 'http://127.0.0.1:8000/mb-admin/products/'
        }
        
        response = session.post(url, data=test_data, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        
        if response.status_code == 201:
            response_data = response.json()
            image_id = response_data.get('id')
            print(f"✅ Successfully created image with ID: {image_id}")
            
            # Check what was actually saved in database
            if image_id:
                try:
                    saved_image = ProductImage.objects.get(id=image_id)
                    print(f"Database record:")
                    print(f"  - Image field: '{saved_image.image}'")
                    print(f"  - Image URL property: '{saved_image.image_url}'")
                    print(f"  - Alt text: '{saved_image.alt_text}'")
                    print(f"  - Is primary: {saved_image.is_primary}")
                except ProductImage.DoesNotExist:
                    print(f"❌ Could not find saved image with ID {image_id}")
        else:
            print(f"❌ Failed to create image")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Django server. Make sure it's running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    test_image_creation()