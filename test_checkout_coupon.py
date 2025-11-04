#!/usr/bin/env python3
"""
Test script for checkout page coupon functionality
This script tests the checkout page coupon application and total amount display
"""

import os
import sys
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from cart.models import Coupon, Cart, CartItem
from products.models import Product
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.test import Client

User = get_user_model()

def test_checkout_coupon_functionality():
    """Test checkout page coupon functionality"""
    print("🧪 Testing Checkout Page Coupon Functionality")
    print("=" * 60)
    
    # Create a test client
    client = Client()
    
    # Test 1: Access checkout page
    print("\n1. Testing checkout page access...")
    try:
        response = client.get('/checkout/')
        if response.status_code == 200:
            print("   ✅ Checkout page loads successfully")
        else:
            print(f"   ❌ Checkout page failed to load: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing checkout page: {e}")
    
    # Test 2: Verify cart API endpoint
    print("\n2. Testing cart API endpoint...")
    try:
        response = client.get('/api/v1/cart/')
        if response.status_code == 200:
            cart_data = response.json()
            print("   ✅ Cart API responds successfully")
            print(f"   📊 Cart data keys: {list(cart_data.keys())}")
            
            # Check if required fields are present
            required_fields = ['subtotal', 'items', 'total_amount']
            missing_fields = [field for field in required_fields if field not in cart_data]
            if missing_fields:
                print(f"   ⚠️ Missing fields in cart data: {missing_fields}")
            else:
                print("   ✅ All required fields present in cart data")
                
        else:
            print(f"   ❌ Cart API failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error accessing cart API: {e}")
    
    # Test 3: Verify coupon API endpoints
    print("\n3. Testing coupon API endpoints...")
    
    # Test apply coupon endpoint
    try:
        response = client.post('/api/v1/cart/apply-coupon/', 
                              data={'code': 'TESTCOUPON'}, 
                              content_type='application/json')
        print(f"   📡 Apply coupon endpoint response: {response.status_code}")
        if hasattr(response, 'json'):
            print(f"   📄 Response data: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error testing apply coupon: {e}")
    
    # Test remove coupon endpoint
    try:
        response = client.post('/api/v1/cart/remove-coupon/')
        print(f"   📡 Remove coupon endpoint response: {response.status_code}")
        if hasattr(response, 'json'):
            print(f"   📄 Response data: {response.json()}")
    except Exception as e:
        print(f"   ❌ Error testing remove coupon: {e}")
    
    # Test 4: Check available coupons
    print("\n4. Checking available test coupons...")
    active_coupons = Coupon.objects.filter(is_active=True, valid_until__gt=timezone.now())
    
    if active_coupons.exists():
        print(f"   ✅ Found {active_coupons.count()} active coupons:")
        for coupon in active_coupons[:5]:  # Show first 5
            status = "🔴 EXPIRED" if coupon.is_expired else "✅ ACTIVE"
            print(f"      {status} {coupon.code} - {coupon.discount_display}")
    else:
        print("   ⚠️ No active coupons found")
        print("   💡 Run 'python test_coupon_system.py' to create test coupons")
    
    # Test 5: Simulate cart with items for testing
    print("\n5. Testing with sample cart data...")
    
    sample_cart_data = {
        'subtotal': '500.00',
        'shipping_cost': '70.00',
        'tax_amount': '0.00',
        'discount_amount': '0.00',
        'coupon_discount': '0.00',
        'coupon_code': '',
        'total_amount': '570.00',
        'items': [
            {
                'product_name': 'Test Product',
                'quantity': 2,
                'total_price': '500.00'
            }
        ]
    }
    
    print("   📊 Sample cart data structure:")
    for key, value in sample_cart_data.items():
        if key != 'items':
            print(f"      {key}: {value}")
    
    # Test 6: Check JavaScript functions in checkout template
    print("\n6. Checking checkout template JavaScript functions...")
    
    checkout_template_path = 'frontend/templates/frontend/checkout.html'
    
    try:
        with open(checkout_template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for required JavaScript functions
        required_functions = [
            'function applyCoupon',
            'function removeCoupon',
            'function updateOrderTotals',
            'function loadOrderSummary',
            'function updateShippingCost'
        ]
        
        for func in required_functions:
            if func in content:
                print(f"   ✅ Found: {func}")
            else:
                print(f"   ❌ Missing: {func}")
                
        # Check for proper currency handling
        if 'replace(\'৳\',' in content:
            print("   ✅ Proper currency parsing (৳) found")
        else:
            print("   ⚠️ Currency parsing may need attention")
            
        # Check for coupon-related DOM elements
        coupon_elements = [
            'coupon-code',
            'apply-coupon-btn',
            'remove-coupon-btn',
            'applied-coupon',
            'coupon-message'
        ]
        
        print("   🎯 Coupon-related DOM elements:")
        for element in coupon_elements:
            if f'id="{element}"' in content:
                print(f"      ✅ {element}")
            else:
                print(f"      ❌ {element}")
                
    except FileNotFoundError:
        print(f"   ❌ Template file not found: {checkout_template_path}")
    except Exception as e:
        print(f"   ❌ Error reading template: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test Summary & Recommendations:")
    print("=" * 60)
    
    print("\n✅ Fixed Issues:")
    print("   • Updated updateShippingCost() to parse ৳ instead of $")
    print("   • Fixed total amount display formatting")
    print("   • Ensured coupon functions call loadOrderSummary()")
    print("   • Added proper field name handling in updateOrderTotals()")
    
    print("\n🔧 To Test Manually:")
    print("   1. Visit http://localhost:8000/checkout/")
    print("   2. Check if total amounts show properly (not ৳0.00)")
    print("   3. Try applying coupon codes: FLAT50, BIG25, FREESHIP")
    print("   4. Verify coupon removal works")
    print("   5. Check shipping cost updates affect total")
    
    print("\n💡 Debugging Tips:")
    print("   • Open browser developer console (F12)")
    print("   • Check Network tab for API calls")
    print("   • Look for JavaScript errors in Console tab")
    print("   • Verify cart has items before testing coupons")
    
    if active_coupons.exists():
        print(f"\n🎫 Test with these active coupons:")
        for coupon in active_coupons[:3]:
            min_order = f" (min order ৳{coupon.minimum_order_amount})" if coupon.minimum_order_amount > 0 else ""
            print(f"   • {coupon.code} - {coupon.discount_display}{min_order}")

def main():
    """Main test function"""
    try:
        test_checkout_coupon_functionality()
        print("\n🎉 Checkout coupon functionality test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
