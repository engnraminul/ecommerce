#!/usr/bin/env python
"""
Test script to create an order with coupon discount for testing
order confirmation and invoice display functionality.
"""

import os
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth.models import User
from orders.models import Order, OrderItem, ShippingAddress
from products.models import Product
from cart.models import Coupon

def create_test_order_with_coupon():
    """Create a test order with coupon for testing."""
    
    # Get or create a test coupon
    coupon, created = Coupon.objects.get_or_create(
        code='FLAT50',
        defaults={
            'name': 'Flat 50 Taka Discount',
            'description': 'Get 50 Taka off on any order',
            'discount_type': 'fixed',
            'discount_value': Decimal('50.00'),
            'minimum_order_amount': Decimal('100.00'),
            'is_active': True,
            'valid_from': django.utils.timezone.now(),
            'valid_until': django.utils.timezone.now() + django.utils.timezone.timedelta(days=30)
        }
    )
    print(f"{'Created' if created else 'Found'} coupon: {coupon.code}")
    
    # Get a test product
    product = Product.objects.filter(is_active=True).first()
    if not product:
        print("No active products found. Please create products first.")
        return None
    
    print(f"Using product: {product.name} - ৳{product.price}")
    
    # Create order first
    order = Order.objects.create(
        customer_email='test@example.com',
        customer_phone='01777173040',
        payment_method='cash_on_delivery',
        payment_status='pending',
        status='pending',
        subtotal=Decimal('1700.00'),  # Base amount before coupon
        shipping_cost=Decimal('0.00'),
        tax_amount=Decimal('0.00'),
        discount_amount=Decimal('0.00'),
        coupon=coupon,
        coupon_code=coupon.code,
        coupon_discount=Decimal('50.00'),  # Apply 50 taka discount
        total_amount=Decimal('1650.00')    # 1700 - 50 = 1650
    )
    
    # Create shipping address linked to the order
    shipping_address = ShippingAddress.objects.create(
        order=order,
        first_name='John',
        last_name='Doe',
        address_line_1='123 Test Street',
        city='Dhaka',
        state='Dhaka',
        postal_code='1000',
        country='Bangladesh',
        phone='01777173040'
    )
    
    # Create order items
    OrderItem.objects.create(
        order=order,
        product=product,
        product_name=product.name,
        product_sku=product.sku,
        unit_price=product.price,
        quantity=1
    )
    
    # If we need more items to reach 1700 subtotal
    remaining_amount = Decimal('1700.00') - product.price
    if remaining_amount > 0:
        # Add more quantity or another product to reach subtotal
        additional_qty = int(remaining_amount / product.price)
        if additional_qty > 0:
            first_item = order.items.first()
            first_item.quantity += additional_qty
            first_item.save()
    
    # Recalculate order totals
    order.calculate_totals()
    order.save()
    
    print(f"Created test order: {order.order_number}")
    print(f"  Subtotal: ৳{order.subtotal}")
    print(f"  Coupon ({order.coupon_code}): -৳{order.coupon_discount}")
    print(f"  Total: ৳{order.total_amount}")
    print(f"  Order URL: /order-confirmation/{order.order_number}/")
    
    return order

if __name__ == '__main__':
    import django.utils.timezone
    order = create_test_order_with_coupon()
    if order:
        print("\nTest order created successfully!")
        print(f"Visit: http://localhost:8000/order-confirmation/{order.order_number}/")
    else:
        print("Failed to create test order.")