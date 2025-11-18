#!/usr/bin/env python
"""
Test script to verify the edit shipping functionality works correctly.
Run this from the Django project directory with: python test_shipping_edit.py
"""

import os
import sys
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order
from orders.order_edit_views import update_shipping_cost
from django.test.client import RequestFactory
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
import json

def test_shipping_edit():
    """Test the shipping cost edit functionality"""
    
    print("Testing Shipping Cost Edit Functionality")
    print("=" * 50)
    
    # Get a sample order (you may need to adjust this based on your data)
    try:
        order = Order.objects.first()
        if not order:
            print("❌ No orders found in database. Please create an order first.")
            return False
            
        print(f"✅ Found test order: {order.order_number}")
        print(f"   Current shipping cost: ৳{order.shipping_cost}")
        print(f"   Current total: ৳{order.total_amount}")
        
        # Create a test request
        factory = APIRequestFactory()
        new_shipping_cost = Decimal('150.00')  # Test with 150 taka
        
        request_data = {
            'shipping_cost': str(new_shipping_cost)
        }
        
        request = factory.post(
            f'/api/orders/{order.id}/edit/shipping/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        # Add a mock admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("❌ No admin user found. Creating a test admin user...")
            admin_user = User.objects.create_superuser(
                username='test_admin',
                email='admin@test.com',
                password='testpass123'
            )
        
        request.user = admin_user
        
        # Test the update function
        print(f"\n🧪 Testing update with new shipping cost: ৳{new_shipping_cost}")
        
        response = update_shipping_cost(request, order.id)
        
        if response.status_code == 200:
            print("✅ API call successful!")
            
            # Refresh the order from database
            order.refresh_from_db()
            print(f"   Updated shipping cost: ৳{order.shipping_cost}")
            print(f"   Updated total: ৳{order.total_amount}")
            
            if order.shipping_cost == new_shipping_cost:
                print("✅ Shipping cost updated correctly!")
                return True
            else:
                print(f"❌ Shipping cost not updated. Expected: {new_shipping_cost}, Got: {order.shipping_cost}")
                return False
        else:
            print(f"❌ API call failed with status: {response.status_code}")
            print(f"   Response: {response.data}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_shipping_edit()
    if success:
        print("\n🎉 All tests passed! The edit shipping functionality is working correctly.")
    else:
        print("\n💥 Tests failed! Please check the implementation.")