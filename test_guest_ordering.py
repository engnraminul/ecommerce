#!/usr/bin/env python3
"""
Test script for guest ordering functionality
"""
import os
import sys
import django
import requests
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.test import TestCase, Client
from django.contrib.sessions.models import Session
from orders.models import Order, OrderItem, ShippingAddress
from cart.models import Cart, CartItem
from products.models import Product, Category, ProductVariant
from users.models import User
import json

class GuestOrderingTest:
    def __init__(self):
        self.client = Client()
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test products and category"""
        print("Setting up test data...")
        
        # Create category
        self.category, created = Category.objects.get_or_create(
            name="Test Category",
            defaults={'slug': 'test-category', 'description': 'Test category for guest ordering'}
        )
        
        # Create product
        self.product, created = Product.objects.get_or_create(
            name="Test Product",
            defaults={
                'slug': 'test-product',
                'description': 'Test product for guest ordering',
                'price': Decimal('29.99'),
                'stock_quantity': 100,
                'category': self.category,
                'is_active': True,
                'track_inventory': True
            }
        )
        print(f"Product created/found: {self.product.name} (ID: {self.product.id})")
    
    def test_guest_add_to_cart(self):
        """Test adding product to cart as guest"""
        print("\n=== Testing Guest Add to Cart ===")
        
        # Add product to cart
        response = self.client.post('/api/v1/cart/add/', {
            'product_id': self.product.id,
            'quantity': 2
        }, content_type='application/json')
        
        print(f"Add to cart response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Guest add to cart: PASSED")
            return True
        else:
            print(f"❌ Guest add to cart: FAILED - {response.content.decode()}")
            return False
    
    def test_guest_view_cart(self):
        """Test viewing cart as guest"""
        print("\n=== Testing Guest View Cart ===")
        
        response = self.client.get('/api/v1/cart/')
        print(f"View cart response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Cart items count: {data.get('total_items', 0)}")
            print("✅ Guest view cart: PASSED")
            return True
        else:
            print(f"❌ Guest view cart: FAILED - {response.content.decode()}")
            return False
    
    def test_guest_checkout(self):
        """Test guest checkout process"""
        print("\n=== Testing Guest Checkout ===")
        
        # First add item to cart
        self.client.post('/api/v1/cart/add/', {
            'product_id': self.product.id,
            'quantity': 1
        }, content_type='application/json')
        
        # Prepare order data
        order_data = {
            'shipping_address': {
                'first_name': 'John',
                'last_name': 'Doe',
                'company': '',
                'address_line_1': '123 Test Street',
                'address_line_2': '',
                'city': 'Dhaka',
                'state': 'Dhaka',
                'postal_code': '1000',
                'country': 'Bangladesh',
                'phone': '01712345678',
                'email': 'john.doe@example.com',
                'delivery_instructions': 'Test order for guest checkout'
            },
            'customer_notes': 'This is a test guest order',
            'coupon_code': '',
            'shipping_option': 'standard',
            'shipping_location': 'dhaka',
            'guest_email': 'john.doe@example.com',
            'guest_phone': '01712345678'
        }
        
        # Create order
        response = self.client.post('/api/v1/orders/create/', 
                                   json.dumps(order_data),
                                   content_type='application/json')
        
        print(f"Create order response status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            order_number = data.get('order', {}).get('order_number')
            print(f"✅ Guest checkout: PASSED - Order created: {order_number}")
            
            # Verify order in database
            if order_number:
                try:
                    order = Order.objects.get(order_number=order_number)
                    print(f"Order verified in database:")
                    print(f"  - Is guest order: {order.is_guest_order}")
                    print(f"  - Customer email: {order.customer_email}")
                    print(f"  - User: {order.user}")
                    print(f"  - Total amount: {order.total_amount}")
                    return True
                except Order.DoesNotExist:
                    print(f"❌ Order {order_number} not found in database")
                    return False
        else:
            error_data = response.json() if response.content else {}
            print(f"❌ Guest checkout: FAILED - {error_data}")
            return False
    
    def test_order_tracking(self):
        """Test order tracking functionality"""
        print("\n=== Testing Order Tracking ===")
        
        # First create a guest order
        self.client.post('/api/v1/cart/add/', {
            'product_id': self.product.id,
            'quantity': 1
        }, content_type='application/json')
        
        order_data = {
            'shipping_address': {
                'first_name': 'Jane',
                'last_name': 'Smith',
                'address_line_1': '456 Track Street',
                'city': 'Dhaka',
                'state': 'Dhaka',
                'postal_code': '1000',
                'country': 'Bangladesh',
                'phone': '01787654321',
                'email': 'jane.smith@example.com'
            },
            'guest_email': 'jane.smith@example.com',
            'guest_phone': '01787654321'
        }
        
        response = self.client.post('/api/v1/orders/create/', 
                                   json.dumps(order_data),
                                   content_type='application/json')
        
        if response.status_code == 201:
            data = response.json()
            order_number = data.get('order', {}).get('order_number')
            
            # Test tracking
            track_response = self.client.get(f'/api/v1/orders/track/{order_number}/')
            print(f"Track order response status: {track_response.status_code}")
            
            if track_response.status_code == 200:
                track_data = track_response.json()
                print(f"✅ Order tracking: PASSED - Order {order_number} tracked successfully")
                return True
            else:
                print(f"❌ Order tracking: FAILED")
                return False
        else:
            print("❌ Could not create order for tracking test")
            return False
    
    def run_all_tests(self):
        """Run all guest ordering tests"""
        print("🧪 Starting Guest Ordering Tests...")
        print("=" * 50)
        
        tests = [
            self.test_guest_add_to_cart,
            self.test_guest_view_cart,
            self.test_guest_checkout,
            self.test_order_tracking
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"🏁 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Guest ordering is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the implementation.")
        
        return passed == total

if __name__ == '__main__':
    tester = GuestOrderingTest()
    tester.run_all_tests()
