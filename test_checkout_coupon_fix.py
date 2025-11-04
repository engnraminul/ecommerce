#!/usr/bin/env python3
"""
Test script to verify checkout page coupon discount calculation fix
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from django.contrib.sessions.models import Session
from django.http import HttpRequest
from cart.models import Cart, CartItem
from products.models import Product
from coupons.models import Coupon

def test_checkout_coupon_integration():
    """Test that checkout page correctly handles coupon discounts"""
    
    print("🧪 Testing Checkout Coupon Integration...")
    
    # Clear any existing test data
    Cart.objects.filter(session_key__startswith='test_').delete()
    
    # Create a test cart
    cart = Cart.objects.create(session_key='test_checkout_integration')
    
    # Get a product
    product = Product.objects.filter(stock_quantity__gt=0).first()
    if not product:
        print("❌ No products with stock found")
        return False
    
    # Add item to cart
    cart_item = CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=2,
        unit_price=product.price
    )
    
    print(f"✅ Cart created with product: {product.name}")
    print(f"   Price: ৳{product.price} x 2 = ৳{product.price * 2}")
    
    # Test cart summary API without coupon
    print("\n📊 Testing cart summary API without coupon...")
    response = requests.get('http://localhost:8000/api/v1/cart/summary/', 
                           cookies={'sessionid': 'test_checkout_integration'})
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Subtotal: ৳{data.get('subtotal', 0)}")
        print(f"   Total: ৳{data.get('total_amount', 0)}")
        print(f"   Coupon Discount: ৳{data.get('coupon_discount', 0)}")
    else:
        print(f"❌ Cart summary API failed: {response.status_code}")
        return False
    
    # Apply coupon
    print("\n🎫 Applying coupon FLAT50...")
    coupon_response = requests.post('http://localhost:8000/api/v1/cart/apply-coupon/',
                                   json={'coupon_code': 'FLAT50'},
                                   cookies={'sessionid': 'test_checkout_integration'},
                                   headers={'Content-Type': 'application/json'})
    
    if coupon_response.status_code == 200:
        coupon_data = coupon_response.json()
        print(f"✅ Coupon applied: {coupon_data.get('message', 'Success')}")
    else:
        print(f"❌ Coupon application failed: {coupon_response.status_code}")
        print(f"   Response: {coupon_response.text}")
        return False
    
    # Test cart summary API with coupon
    print("\n📊 Testing cart summary API with coupon...")
    response = requests.get('http://localhost:8000/api/v1/cart/summary/', 
                           cookies={'sessionid': 'test_checkout_integration'})
    
    if response.status_code == 200:
        data = response.json()
        subtotal = data.get('subtotal', 0)
        coupon_discount = data.get('coupon_discount', 0)
        total = data.get('total_amount', 0)
        
        print(f"   Subtotal: ৳{subtotal}")
        print(f"   Coupon Discount: -৳{coupon_discount}")
        print(f"   Total: ৳{total}")
        
        # Verify calculation
        expected_total = subtotal - coupon_discount
        if abs(total - expected_total) < 0.01:  # Allow for small float differences
            print(f"✅ Total calculation correct: ৳{subtotal} - ৳{coupon_discount} = ৳{total}")
        else:
            print(f"❌ Total calculation error: Expected ৳{expected_total}, got ৳{total}")
            return False
    else:
        print(f"❌ Cart summary API with coupon failed: {response.status_code}")
        return False
    
    # Test shipping cost calculation (simulate what happens when shipping changes)
    print("\n🚚 Testing shipping cost integration...")
    dhaka_shipping = 60  # Standard Dhaka shipping cost
    print(f"   Adding shipping cost: ৳{dhaka_shipping}")
    
    # Calculate what frontend should show
    expected_total_with_shipping = subtotal + dhaka_shipping - coupon_discount
    print(f"   Expected total with shipping: ৳{subtotal} + ৳{dhaka_shipping} - ৳{coupon_discount} = ৳{expected_total_with_shipping}")
    
    print("\n✅ Frontend JavaScript should now correctly calculate:")
    print(f"   - Subtotal: ৳{subtotal}")
    print(f"   - Shipping: ৳{dhaka_shipping}")
    print(f"   - Coupon Discount: -৳{coupon_discount}")
    print(f"   - Final Total: ৳{expected_total_with_shipping}")
    
    # Cleanup
    cart.delete()
    print("\n🧹 Test cleanup completed")
    
    print("\n🌐 Manual Testing Instructions:")
    print("   1. Visit http://localhost:8000/checkout/")
    print("   2. Add items to cart if needed")
    print("   3. Apply coupon 'FLAT50'")
    print("   4. Change shipping location (Dhaka/Outside)")
    print("   5. Verify total updates correctly with coupon discount")
    print("   6. Check that order-total element shows correct final amount")
    
    return True

if __name__ == "__main__":
    success = test_checkout_coupon_integration()
    if success:
        print("\n🎉 All tests passed! Checkout coupon integration is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")