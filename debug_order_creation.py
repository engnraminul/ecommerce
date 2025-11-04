#!/usr/bin/env python
"""
Debug script to test order creation API endpoint.
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User
from products.models import Product
from cart.models import Cart, CartItem, Coupon

def test_order_creation():
    """Test order creation with minimal data."""
    
    from django.test import Client
    
    # Create Django test client
    client = Client()
    
    # First, create a cart with items
    print("Setting up test cart...")
    
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
    
    # Test order creation payload
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
        "customer_notes": "Test order",
        "coupon_code": "",
        "shipping_option": "",
        "shipping_location": "dhaka",
        "guest_email": "test@example.com",
        "guest_phone": "01777173040",
        "payment_method": "cod",
        "payment_method_display_name": "Cash on Delivery"
    }
    
    print("Testing order creation API...")
    print("Order data:", json.dumps(order_data, indent=2))
    
    # Test with Django client
    try:
        response = client.post('/api/v1/orders/create/', 
                              data=json.dumps(order_data), 
                              content_type='application/json')
        
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content.decode('utf-8')[:500]}...")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print("Order created successfully!")
            print(f"Order data: {json.dumps(result, indent=2)}")
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

if __name__ == '__main__':
    test_order_creation()