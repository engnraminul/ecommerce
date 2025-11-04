#!/usr/bin/env python3
"""
Test script for the comprehensive coupon system
This script creates sample coupons and tests the basic functionality
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from cart.models import Coupon, CouponUsage
from orders.models import Order
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def create_test_coupons():
    """Create sample coupons for testing"""
    print("🎫 Creating test coupons...")
    
    # Get or create a superuser for testing
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                'admin', 'admin@example.com', 'admin123'
            )
    except Exception as e:
        print(f"Using anonymous user for coupon creation: {e}")
        admin_user = None
    
    # Sample coupons data
    sample_coupons = [
        {
            'code': 'WELCOME10',
            'name': 'Welcome 10% Off',
            'description': 'Get 10% off your first order',
            'discount_type': 'percentage',
            'discount_value': Decimal('10.00'),
            'minimum_order_amount': Decimal('100.00'),
            'maximum_discount_amount': Decimal('50.00'),
            'usage_limit': 100,
            'usage_limit_per_user': 1,
        },
        {
            'code': 'FLAT50',
            'name': 'Flat ৳50 Off',
            'description': 'Flat ৳50 discount on orders above ৳200',
            'discount_type': 'flat',
            'discount_value': Decimal('50.00'),
            'minimum_order_amount': Decimal('200.00'),
            'usage_limit': 50,
            'usage_limit_per_user': 2,
        },
        {
            'code': 'FREESHIP',
            'name': 'Free Shipping',
            'description': 'Free shipping on all orders',
            'discount_type': 'free_shipping',
            'discount_value': Decimal('0.00'),
            'minimum_order_amount': Decimal('0.00'),
            'usage_limit': None,  # Unlimited
            'usage_limit_per_user': 5,
        },
        {
            'code': 'BIG25',
            'name': 'Big Sale 25% Off',
            'description': 'Special 25% discount for big purchases',
            'discount_type': 'percentage',
            'discount_value': Decimal('25.00'),
            'minimum_order_amount': Decimal('500.00'),
            'maximum_discount_amount': Decimal('200.00'),
            'usage_limit': 20,
            'usage_limit_per_user': 1,
        },
        {
            'code': 'EXPIRED10',
            'name': 'Expired Coupon',
            'description': 'This coupon has expired (for testing)',
            'discount_type': 'percentage',
            'discount_value': Decimal('10.00'),
            'minimum_order_amount': Decimal('0.00'),
            'usage_limit': 10,
            'usage_limit_per_user': 1,
            'expired': True,  # Special flag for expired coupon
        }
    ]
    
    created_coupons = []
    
    for coupon_data in sample_coupons:
        # Calculate validity dates
        valid_from = timezone.now()
        if coupon_data.get('expired'):
            # Create an expired coupon
            valid_from = timezone.now() - timedelta(days=30)
            valid_until = timezone.now() - timedelta(days=1)
            del coupon_data['expired']
        else:
            # Valid for 30 days
            valid_until = timezone.now() + timedelta(days=30)
        
        # Check if coupon already exists
        existing_coupon = Coupon.objects.filter(code=coupon_data['code']).first()
        if existing_coupon:
            print(f"   ⚠️ Coupon {coupon_data['code']} already exists, skipping...")
            created_coupons.append(existing_coupon)
            continue
        
        try:
            coupon = Coupon.objects.create(
                **coupon_data,
                valid_from=valid_from,
                valid_until=valid_until,
                is_active=True,
                created_by=admin_user
            )
            created_coupons.append(coupon)
            
            status = "🔴 EXPIRED" if coupon.is_expired else "✅ ACTIVE"
            print(f"   ✅ Created: {coupon.code} - {coupon.name} ({status})")
            
        except Exception as e:
            print(f"   ❌ Error creating coupon {coupon_data['code']}: {e}")
    
    return created_coupons

def test_coupon_validation():
    """Test coupon validation logic"""
    print("\n🧪 Testing coupon validation...")
    
    # Test various scenarios
    test_scenarios = [
        {
            'code': 'WELCOME10',
            'cart_total': Decimal('150.00'),
            'expected': True,
            'description': 'Valid coupon with sufficient order amount'
        },
        {
            'code': 'WELCOME10',
            'cart_total': Decimal('50.00'),
            'expected': False,
            'description': 'Valid coupon but insufficient order amount'
        },
        {
            'code': 'FLAT50',
            'cart_total': Decimal('250.00'),
            'expected': True,
            'description': 'Flat discount coupon'
        },
        {
            'code': 'EXPIRED10',
            'cart_total': Decimal('100.00'),
            'expected': False,
            'description': 'Expired coupon'
        },
        {
            'code': 'NONEXISTENT',
            'cart_total': Decimal('100.00'),
            'expected': False,
            'description': 'Non-existent coupon'
        }
    ]
    
    for scenario in test_scenarios:
        try:
            coupon = Coupon.objects.get(code=scenario['code'])
            is_valid, message = coupon.is_valid(cart_total=scenario['cart_total'])
        except Coupon.DoesNotExist:
            is_valid = False
            message = "Coupon not found"
        
        result = "✅ PASS" if is_valid == scenario['expected'] else "❌ FAIL"
        print(f"   {result} {scenario['description']}")
        print(f"      Code: {scenario['code']}, Cart: ৳{scenario['cart_total']}")
        print(f"      Result: {is_valid}, Message: {message}")

def test_discount_calculation():
    """Test discount calculation for different coupon types"""
    print("\n💰 Testing discount calculations...")
    
    test_scenarios = [
        {
            'code': 'WELCOME10',
            'cart_total': Decimal('200.00'),
            'expected_discount': Decimal('20.00'),  # 10% of 200
            'description': 'Percentage discount calculation'
        },
        {
            'code': 'FLAT50',
            'cart_total': Decimal('300.00'),
            'expected_discount': Decimal('50.00'),  # Flat 50
            'description': 'Flat discount calculation'
        },
        {
            'code': 'BIG25',
            'cart_total': Decimal('1000.00'),
            'expected_discount': Decimal('200.00'),  # 25% but capped at 200
            'description': 'Percentage with maximum discount cap'
        }
    ]
    
    for scenario in test_scenarios:
        try:
            coupon = Coupon.objects.get(code=scenario['code'])
            discount = coupon.calculate_discount(scenario['cart_total'])
            
            result = "✅ PASS" if discount == scenario['expected_discount'] else "❌ FAIL"
            print(f"   {result} {scenario['description']}")
            print(f"      Code: {scenario['code']}, Cart: ৳{scenario['cart_total']}")
            print(f"      Expected: ৳{scenario['expected_discount']}, Got: ৳{discount}")
            
        except Coupon.DoesNotExist:
            print(f"   ❌ FAIL Coupon {scenario['code']} not found")

def display_coupon_summary():
    """Display summary of created coupons"""
    print("\n📊 Coupon Summary:")
    print("=" * 80)
    
    coupons = Coupon.objects.all().order_by('-created_at')
    
    if not coupons:
        print("   No coupons found in the database.")
        return
    
    for coupon in coupons:
        status = "🔴 EXPIRED" if coupon.is_expired else "✅ ACTIVE"
        usage_info = f"{coupon.used_count}"
        if coupon.usage_limit:
            usage_info += f"/{coupon.usage_limit}"
        
        print(f"   {status} {coupon.code} - {coupon.name}")
        print(f"      Type: {coupon.get_discount_type_display()}")
        print(f"      Discount: {coupon.discount_display}")
        print(f"      Min Order: ৳{coupon.minimum_order_amount}")
        print(f"      Usage: {usage_info}")
        print(f"      Valid Until: {coupon.valid_until.strftime('%Y-%m-%d %H:%M')}")
        print()

def main():
    """Main test function"""
    print("🎯 Comprehensive Coupon System Test")
    print("=" * 50)
    
    try:
        # Create test coupons
        created_coupons = create_test_coupons()
        
        # Test coupon validation
        test_coupon_validation()
        
        # Test discount calculations
        test_discount_calculation()
        
        # Display summary
        display_coupon_summary()
        
        print("\n🎉 Coupon system test completed!")
        print("\nNext Steps:")
        print("1. Visit /dashboard/coupons/ to manage coupons via the admin interface")
        print("2. Test coupon application in the frontend cart and checkout")
        print("3. Create an order with a coupon to test the complete flow")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()