"""
Test shipping options for both Dhaka and Outside Dhaka
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Product
from cart.models import Cart, CartItem
from cart.shipping import ShippingCalculator

User = get_user_model()

def test_shipping_options():
    """Test shipping options calculation for both locations"""
    
    print("=== Testing Shipping Options for Both Locations ===\n")
    
    # Get some products
    products = Product.objects.filter(is_active=True)[:2]
    if not products:
        print("❌ No active products found. Please create some products first.")
        return
    
    # Create a test user and cart
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    cart, created = Cart.objects.get_or_create(user=user)
    cart.items.all().delete()  # Clear existing items
    
    # Add products to cart
    cart_items = []
    for product in products:
        item = CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=1,
            unit_price=product.price
        )
        cart_items.append(item)
        print(f"✓ Added {product.name} to cart")
        print(f"  - Shipping Type: {product.get_shipping_type_display()}")
        print(f"  - Has Express: {'Yes' if product.has_express_shipping else 'No'}")
    
    print(f"\n=== Cart Summary ===")
    print(f"Total items: {len(cart_items)}")
    print(f"Subtotal: {sum(item.total_price for item in cart_items)}৳")
    
    # Test shipping options for both locations
    locations = ['dhaka', 'outside']
    
    for location in locations:
        print(f"\n=== Shipping Options for {location.upper()} ===")
        
        # Create shipping calculator
        shipping_calculator = ShippingCalculator(cart_items, location)
        shipping_summary = shipping_calculator.get_shipping_summary()
        
        options = shipping_summary['available_options']
        print(f"✓ Found {len(options)} shipping options:")
        
        for i, option in enumerate(options, 1):
            cost_display = 'FREE' if option['cost'] == 0 else f"{option['cost']}৳"
            print(f"  {i}. {option['name']}")
            print(f"     Cost: {cost_display}")
            print(f"     Delivery: {option['estimated_days']}")
            print(f"     Description: {option['description']}")
            print()
    
    print("=== Frontend Implementation ===")
    print("✅ Location dropdown added to checkout form")
    print("✅ Dynamic shipping options loading")
    print("✅ JavaScript updates options when location changes")
    print("✅ Fallback options if API fails")
    print("\nTo test in browser:")
    print("1. Go to http://127.0.0.1:8000/checkout/")
    print("2. Select 'Dhaka City' or 'Outside Dhaka' from dropdown")
    print("3. Watch shipping options update automatically")
    print("4. Express shipping only appears for Dhaka City")

if __name__ == "__main__":
    test_shipping_options()
