#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from orders.models import Order
import json

def test_variant_fix():
    """Test that the variant fix is working correctly"""
    print("Testing Order Item Variant Fix")
    print("=" * 40)
    
    # Get admin user
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    client = Client()
    client.force_login(user)
    
    # Find order with variant items
    order = Order.objects.filter(items__variant__isnull=False).first()
    if not order:
        print("❌ No orders with variants found")
        return
    
    print(f"✅ Testing with order: {order.order_number}")
    
    # Test order items API
    response = client.get(f'/mb-admin/api/orders/{order.id}/items/')
    if response.status_code != 200:
        print(f"❌ Order items API failed: {response.status_code}")
        return
    
    items = response.json()
    variant_item = None
    
    for item in items:
        if item.get('variant'):
            variant_item = item
            break
    
    if not variant_item:
        print("❌ No variant items found in response")
        return
    
    print(f"✅ Found variant item: {variant_item['product_name']}")
    print(f"✅ Item has product field: {'product' in variant_item}")
    print(f"✅ Item has variant field: {'variant' in variant_item}")
    print(f"✅ Product ID: {variant_item.get('product')}")
    print(f"✅ Variant ID: {variant_item.get('variant')}")
    
    # Test product API
    product_id = variant_item.get('product')
    response = client.get(f'/mb-admin/api/products/{product_id}/')
    if response.status_code != 200:
        print(f"❌ Product API failed: {response.status_code}")
        return
    
    product_data = response.json()
    if 'variants' not in product_data:
        print("❌ Product response missing variants field")
        return
    
    variants = product_data['variants']
    print(f"✅ Product API returned {len(variants)} variants")
    
    # Show what the JavaScript dropdown would see
    print("\n📋 Variant Dropdown Options:")
    print("   <option value=''>No variant</option>")
    
    current_variant_id = variant_item.get('variant')
    for variant in variants:
        selected = " selected" if variant['id'] == current_variant_id else ""
        print(f"   <option value='{variant['id']}'{selected}>{variant['name']}</option>")
    
    print(f"\n🎉 SUCCESS! Variant loading is now working correctly!")
    print(f"   - Order items include product and variant fields")
    print(f"   - Product API returns variants data")
    print(f"   - JavaScript can now populate the dropdown")

if __name__ == '__main__':
    test_variant_fix()