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

def test_before_after():
    print("=== TESTING BEFORE AND AFTER IMAGE COUNTS ===\n")
    
    # Get first product
    product = Product.objects.first()
    print(f"Testing with product: {product.name} (ID: {product.id})")
    
    # Check initial state
    initial_count = product.images.count()
    print(f"Initial image count: {initial_count}")
    
    # List current images
    if initial_count > 0:
        print("Current images:")
        for img in product.images.all():
            print(f"  - ID: {img.id}, Image: '{img.image}', Primary: {img.is_primary}")
    
    print(f"\n✅ Ready for frontend testing!")
    print(f"1. Go to http://127.0.0.1:8000/mb-admin/products/")
    print(f"2. Click 'Edit' on '{product.name}'")
    print(f"3. Click 'Choose from Media Library' button")
    print(f"4. Select an image from the library")
    print(f"5. Click 'Use Selected'")
    print(f"6. Click 'Update Product'")
    print(f"7. Check the console for debugging output")
    print(f"8. Run this script again to see if the count increased")
    
    return product.id, initial_count

def check_after_test(product_id, expected_initial_count):
    print(f"\n=== CHECKING RESULTS AFTER FRONTEND TEST ===\n")
    
    product = Product.objects.get(id=product_id)
    final_count = product.images.count()
    
    print(f"Product: {product.name}")
    print(f"Initial count: {expected_initial_count}")
    print(f"Final count: {final_count}")
    print(f"Images added: {final_count - expected_initial_count}")
    
    if final_count > expected_initial_count:
        print(f"✅ SUCCESS! Images were saved to database")
        print(f"New images:")
        for img in product.images.order_by('-id')[:final_count - expected_initial_count]:
            print(f"  - ID: {img.id}, Image: '{img.image}', Alt: '{img.alt_text}'")
    else:
        print(f"❌ No new images detected. Check console for JavaScript errors.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'after':
        # Get the product ID and initial count from command line or use defaults
        product_id = int(sys.argv[2]) if len(sys.argv) > 2 else 26
        initial_count = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        check_after_test(product_id, initial_count)
    else:
        product_id, initial_count = test_before_after()
        print(f"\nTo check results after testing, run:")
        print(f"python test_frontend_complete.py after {product_id} {initial_count}")