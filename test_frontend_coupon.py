#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order
import json

print("=== TESTING FRONTEND COUPON DISPLAY ===")

# Get an order with coupon to test
order_with_coupon = Order.objects.filter(coupon_code__isnull=False).exclude(coupon_code='').first()

if order_with_coupon:
    print(f"\nOrder: {order_with_coupon.order_number}")
    print(f"Expected JavaScript behavior:")
    print(f"  1. orderDetailSubtotal: ৳{order_with_coupon.subtotal}")
    print(f"  2. orderDetailCouponRow: should be visible")
    print(f"  3. orderDetailCouponCode: {order_with_coupon.coupon_code}")
    print(f"  4. orderDetailCouponDiscount: -৳{order_with_coupon.coupon_discount}")
    print(f"  5. orderDetailGrandTotal: ৳{order_with_coupon.total_amount}")
    
    # Calculate what JavaScript should calculate
    subtotal = float(order_with_coupon.subtotal)
    shipping = float(order_with_coupon.shipping_cost or 0)
    tax = float(order_with_coupon.tax_amount or 0)
    coupon_discount = float(order_with_coupon.coupon_discount or 0)
    
    calculated_total = subtotal + shipping + tax - coupon_discount
    print(f"\nCalculation verification:")
    print(f"  Subtotal: ৳{subtotal:.2f}")
    print(f"  Shipping: ৳{shipping:.2f}")
    print(f"  Tax: ৳{tax:.2f}")
    print(f"  Coupon Discount: -৳{coupon_discount:.2f}")
    print(f"  Calculated Total: ৳{calculated_total:.2f}")
    print(f"  Database Total: ৳{float(order_with_coupon.total_amount):.2f}")
    print(f"  Match: {'✓' if abs(calculated_total - float(order_with_coupon.total_amount)) < 0.01 else '✗'}")
    
    # Create a mock order data as JavaScript would receive it
    mock_js_data = {
        'order_number': order_with_coupon.order_number,
        'subtotal': str(order_with_coupon.subtotal),
        'shipping_cost': str(order_with_coupon.shipping_cost or 0),
        'tax_amount': str(order_with_coupon.tax_amount or 0),
        'coupon_code': order_with_coupon.coupon_code,
        'coupon_discount': str(order_with_coupon.coupon_discount),
        'total_amount': str(order_with_coupon.total_amount)
    }
    
    print(f"\nMock API Response (what JavaScript receives):")
    print(json.dumps(mock_js_data, indent=2))
    
else:
    print("No orders with coupons found")