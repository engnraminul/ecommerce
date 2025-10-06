#!/usr/bin/env python
"""
Test script to verify payment method functionality
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order, ProductVariant
from orders.serializers import CreateOrderSerializer
import json

def test_payment_method_functionality():
    """Test the payment method functionality"""
    print("=== Testing Payment Method Functionality ===")
    
    # Get a variant for testing
    try:
        variant = ProductVariant.objects.first()
        if not variant:
            print("❌ No product variants found. Please create some products first.")
            return False
            
        print(f"✅ Using variant: {variant.id} - {variant.name}")
        
        # Test order data with bKash payment method
        order_data = {
            'items': [
                {'variant_id': variant.id, 'quantity': 1}
            ],
            'shipping_address': {
                'first_name': 'Test',
                'last_name': 'User',
                'address_line_1': 'Test Address',
                'city': 'Dhaka',
                'state': 'Dhaka',
                'postal_code': '1000',
                'country': 'Bangladesh',
                'phone': '01700000000',
                'email': 'test@example.com'
            },
            'customer_notes': 'Test order with bKash payment',
            'payment_method': 'bkash',
            'payment_method_display_name': 'bKash',
            'bkash_transaction_id': 'TXN123456789',
            'bkash_sender_number': '01700000000',
            'guest_email': 'test@example.com',
            'guest_phone': '01700000000'
        }
        
        print("📝 Creating order with bKash payment method...")
        
        # Create order using serializer
        serializer = CreateOrderSerializer(data=order_data)
        if serializer.is_valid():
            order = serializer.save()
            print(f"✅ Order created successfully: {order.order_number}")
            print(f"💳 Payment method: {order.payment_method}")
            print(f"📝 Payment display name: {order.payment_method_display_name}")
            print(f"🆔 bKash transaction ID: {order.bkash_transaction_id}")
            print(f"📱 bKash sender number: {order.bkash_sender_number}")
            
            # Test dashboard serializer includes payment method fields
            from dashboard.serializers import OrderDashboardSerializer
            dashboard_data = OrderDashboardSerializer(order).data
            
            print("\n📊 Dashboard serializer includes payment fields:")
            payment_fields = [
                'payment_method', 'payment_method_display_name', 
                'bkash_transaction_id', 'bkash_sender_number'
            ]
            for field in payment_fields:
                if field in dashboard_data:
                    print(f"  ✅ {field}: {dashboard_data[field]}")
                else:
                    print(f"  ❌ {field}: Missing from serializer")
            
            return True
        else:
            print("❌ Validation errors:", serializer.errors)
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_cod_payment():
    """Test COD payment method"""
    print("\n=== Testing COD Payment Method ===")
    
    try:
        variant = ProductVariant.objects.first()
        if not variant:
            return False
            
        order_data = {
            'items': [
                {'variant_id': variant.id, 'quantity': 1}
            ],
            'shipping_address': {
                'first_name': 'COD',
                'last_name': 'Customer',
                'address_line_1': 'COD Address',
                'city': 'Dhaka',
                'state': 'Dhaka',
                'postal_code': '1000',
                'country': 'Bangladesh',
                'phone': '01700000001',
                'email': 'cod@example.com'
            },
            'customer_notes': 'Test order with COD payment',
            'payment_method': 'cod',
            'payment_method_display_name': 'Cash on Delivery',
            'guest_email': 'cod@example.com',
            'guest_phone': '01700000001'
        }
        
        print("📝 Creating order with COD payment method...")
        
        serializer = CreateOrderSerializer(data=order_data)
        if serializer.is_valid():
            order = serializer.save()
            print(f"✅ COD Order created: {order.order_number}")
            print(f"💳 Payment method: {order.payment_method}")
            print(f"📝 Payment display name: {order.payment_method_display_name}")
            return True
        else:
            print("❌ COD Validation errors:", serializer.errors)
            return False
            
    except Exception as e:
        print(f"❌ COD Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Payment Method Tests...\n")
    
    bkash_success = test_payment_method_functionality()
    cod_success = test_cod_payment()
    
    print(f"\n📊 Test Results:")
    print(f"  bKash Payment: {'✅ PASSED' if bkash_success else '❌ FAILED'}")
    print(f"  COD Payment: {'✅ PASSED' if cod_success else '❌ FAILED'}")
    
    if bkash_success and cod_success:
        print("\n🎉 All payment method tests passed!")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        
    # Show recent orders with payment methods
    print("\n📋 Recent orders with payment methods:")
    recent_orders = Order.objects.filter(
        payment_method__isnull=False
    ).order_by('-created_at')[:5]
    
    for order in recent_orders:
        print(f"  📦 {order.order_number}: {order.payment_method} ({order.payment_method_display_name})")
        if order.payment_method == 'bkash':
            print(f"    🆔 TXN: {order.bkash_transaction_id}, 📱 Sender: {order.bkash_sender_number}")