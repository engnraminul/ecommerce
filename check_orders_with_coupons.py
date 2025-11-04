#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from orders.models import Order

print("=== ORDERS WITH COUPONS ===")
orders_with_coupons = Order.objects.filter(coupon_code__isnull=False).exclude(coupon_code='')

if orders_with_coupons.exists():
    for order in orders_with_coupons:
        print(f"\nOrder: {order.order_number}")
        print(f"Coupon Code: {order.coupon_code}")
        print(f"Coupon Discount: ৳{order.coupon_discount}")
        print(f"Subtotal: ৳{order.subtotal}")
        print(f"Shipping: ৳{order.shipping_cost}")
        print(f"Total: ৳{order.total_amount}")
        print(f"Created: {order.created_at}")
        print(f"Status: {order.status}")
        print("-" * 50)
else:
    print("No orders with coupons found.")

print(f"\nTotal orders with coupons: {orders_with_coupons.count()}")