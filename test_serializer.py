#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from dashboard.serializers import OrderDashboardSerializer
from orders.models import Order

print("=== TESTING SERIALIZER COUPON FIELDS ===")

# Get an order with coupon
order_with_coupon = Order.objects.filter(coupon_code__isnull=False).exclude(coupon_code='').first()

if order_with_coupon:
    print(f"\nTesting with order: {order_with_coupon.order_number}")
    print(f"Model data:")
    print(f"  Coupon Code: {order_with_coupon.coupon_code}")
    print(f"  Coupon Discount: {order_with_coupon.coupon_discount}")
    print(f"  Subtotal: {order_with_coupon.subtotal}")
    print(f"  Total: {order_with_coupon.total_amount}")
    
    # Test serializer
    serializer = OrderDashboardSerializer(order_with_coupon)
    serialized_data = serializer.data
    
    print(f"\nSerialized data:")
    print(f"  Coupon Code: {serialized_data.get('coupon_code', 'NOT INCLUDED')}")
    print(f"  Coupon Discount: {serialized_data.get('coupon_discount', 'NOT INCLUDED')}")
    print(f"  Subtotal: {serialized_data.get('subtotal', 'NOT INCLUDED')}")
    print(f"  Total: {serialized_data.get('total_amount', 'NOT INCLUDED')}")
    
    # Check if coupon fields are in the fields list
    print(f"\nSerializer fields include:")
    for field in OrderDashboardSerializer.Meta.fields:
        if 'coupon' in field or 'subtotal' in field:
            print(f"  ✓ {field}")
else:
    print("No orders with coupons found")