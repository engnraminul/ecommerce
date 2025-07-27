"""
Test script to verify shipping functionality
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product
from cart.shipping import ShippingCalculator


def test_shipping_functionality():
    """Test the new checkbox-based shipping functionality"""
    
    print("=== Testing New Checkbox-Based Shipping Functionality ===\n")
    
    # Get some products
    products = Product.objects.filter(is_active=True)[:3]
    
    if not products:
        print("No active products found. Please create some products first.")
        return
    
    # Update products to demonstrate different shipping configurations
    if products:
        print("=== Setting Test Shipping Configurations ===\n")
        
        # Product 1: Free shipping (no express)
        products[0].shipping_type = 'free'
        products[0].has_express_shipping = False
        products[0].save()
        print(f"✓ {products[0].name}")
        print("  - Main: FREE SHIPPING")
        print("  - Express: Not Available")
        
        # Product 2: Standard shipping + Express checkbox enabled
        if len(products) > 1:
            products[1].shipping_type = 'standard'
            products[1].has_express_shipping = True
            products[1].custom_shipping_dhaka = 80
            products[1].custom_shipping_outside = 130
            products[1].custom_express_shipping = 180
            products[1].save()
            print(f"\n✓ {products[1].name}")
            print("  - Main: STANDARD SHIPPING (Custom: Dhaka 80৳, Outside 130৳)")
            print("  - Express: ✓ ENABLED (Custom: 180৳)")
        
        # Product 3: Standard shipping (no express)
        if len(products) > 2:
            products[2].shipping_type = 'standard'
            products[2].has_express_shipping = False
            products[2].save()
            print(f"\n✓ {products[2].name}")
            print("  - Main: STANDARD SHIPPING (Default: Dhaka 70৳, Outside 120৳)")
            print("  - Express: Not Available")
    
    # Test shipping options for different configurations
    print("\n=== Testing Shipping Options ===\n")
    
    for product in products:
        print(f"Product: {product.name}")
        
        # Test for Dhaka
        dhaka_options = product.get_available_shipping_options('dhaka')
        print(f"  Dhaka options: {len(dhaka_options)} available")
        for option in dhaka_options:
            print(f"    - {option['name']}: {option['cost']}৳ ({option['estimated_days']})")
        
        # Test for Outside Dhaka
        outside_options = product.get_available_shipping_options('outside')
        print(f"  Outside Dhaka options: {len(outside_options)} available")
        for option in outside_options:
            print(f"    - {option['name']}: {option['cost']}৳ ({option['estimated_days']})")
        
        print("-" * 60)
    
    print("\n=== New Checkbox System Features ===")
    print("✓ Main Shipping: Choose either 'Free' OR 'Standard with Charge'")
    print("✓ Express Shipping: Independent checkbox - can be added to any product")
    print("✓ Express available only in Dhaka when checkbox is enabled")
    print("✓ Custom cost overrides available for all shipping types")
    print("\n=== Admin Interface ===")
    print("1. Go to /admin/products/product/ to see the new checkbox system")
    print("2. 'Shipping Type': Radio buttons for Free OR Standard")
    print("3. 'Has Express Shipping': Checkbox to enable express option")
    print("4. Custom cost fields for overriding default prices")
    
    print("\n=== Frontend Integration ===")
    print("- Checkout page will show main shipping + express (if enabled)")
    print("- Express only appears for Dhaka location when products support it")
    print("- Cart with mixed products shows appropriate combined options")


if __name__ == "__main__":
    test_shipping_functionality()
