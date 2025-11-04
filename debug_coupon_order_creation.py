#!/usr/bin/env python
"""
Debug script to test order creation API endpoint with coupon.
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from products.models import Product
from cart.models import Cart, CartItem, Coupon
from decimal import Decimal

def test_order_creation_with_coupon():
    """Test order creation with coupon."""
    
    # Create Django test client
    client = Client()
    
    # First, create a cart with items
    print("Setting up test cart with coupon...")
    
    # Get a test product
    product = Product.objects.filter(is_active=True).first()
    if not product:
        print("No active products found!")
        return
    
    print(f"Using product: {product.name} - ৳{product.price}")
    
    # Start a session
    response = client.get('/')  # This will create a session
    session = client.session
    session_key = session.session_key
    
    print(f"Session key: {session_key}")
    
    # Create cart with session
    cart, created = Cart.objects.get_or_create(
        session_id=session_key,
        user=None
    )
    
    # Clear existing items
    cart.items.all().delete()
    
    # Add item to cart
    CartItem.objects.create(
        cart=cart,
        product=product,
        quantity=2
    )
    
    print(f"Cart created with {cart.items.count()} items")
    print(f"Cart subtotal: ৳{cart.subtotal}")
    
    # Get the FLAT50 coupon
    coupon = Coupon.objects.filter(code='FLAT50').first()
    if not coupon:
        print("FLAT50 coupon not found!")
        return
    
    print(f"Using coupon: {coupon.code} - ৳{coupon.discount_value} discount")
    
    # Test order creation payload WITH COUPON
    order_data = {
        "shipping_address": {
            "first_name": "Test",
            "last_name": "User", 
            "address_line_1": "123 Test Street",
            "city": "Dhaka",
            "state": "Dhaka",
            "postal_code": "1000",
            "country": "Bangladesh",
            "phone": "01777173040",
            "email": "test@example.com"
        },
        "customer_notes": "Test order with coupon",
        "coupon_code": "FLAT50",  # Include coupon code
        "shipping_option": "",
        "shipping_location": "dhaka",
        "guest_email": "test@example.com",
        "guest_phone": "01777173040",
        "payment_method": "cod",
        "payment_method_display_name": "Cash on Delivery"
    }
    
    print("Testing order creation API with coupon...")
    print("Order data:", json.dumps(order_data, indent=2))
    
    # Test with Django client
    try:
        response = client.post('/api/v1/orders/create/', 
                              data=json.dumps(order_data), 
                              content_type='application/json')
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print("Order created successfully!")
            order = result['order']
            print(f"Order number: {order['order_number']}")
            print(f"Subtotal: ৳{order['subtotal']}")
            print(f"Coupon code: {order['coupon_code']}")
            print(f"Coupon discount: ৳{order['coupon_discount']}")
            print(f"Total amount: ৳{order['total_amount']}")
            
            # Verify coupon was applied correctly
            expected_total = float(order['subtotal']) - float(order['coupon_discount'])
            actual_total = float(order['total_amount'])
            print(f"Expected total: ৳{expected_total}")
            print(f"Actual total: ৳{actual_total}")
            
            if abs(expected_total - actual_total) < 0.01:
                print("✅ Coupon calculation is correct!")
            else:
                print("❌ Coupon calculation mismatch!")
                
            return order['order_number']
        else:
            print(f"Order creation failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.content.decode('utf-8')}")
                
    except Exception as e:
        print(f"Error testing order creation: {e}")
        import traceback
        traceback.print_exc()
        
    return None

if __name__ == '__main__':
    order_number = test_order_creation_with_coupon()
    if order_number:
        print(f"\n🎉 Test successful! Check order confirmation at:")
        print(f"http://127.0.0.1:8000/order-confirmation/{order_number}/")