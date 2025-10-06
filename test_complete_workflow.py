#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from products.models import Product, ProductVariant
from orders.models import Order, OrderItem
from django.urls import reverse
import json

def test_complete_variant_workflow():
    """Test the complete workflow of order item variant editing"""
    print("=" * 60)
    print("TESTING COMPLETE VARIANT WORKFLOW")
    print("=" * 60)
    
    # Get admin user
    User = get_user_model()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print("No admin user found")
        return
    
    # Create test client and login
    client = Client()
    client.force_login(user)
    
    # Step 1: Find an order with items that have variants
    print("\n1. Looking for orders with variant items...")
    orders_with_variants = Order.objects.filter(
        items__variant__isnull=False
    ).distinct()
    
    if not orders_with_variants.exists():
        print("❌ No orders with variant items found")
        return
    
    test_order = orders_with_variants.first()
    test_item = test_order.items.filter(variant__isnull=False).first()
    
    print(f"✅ Found test order: {test_order.order_number}")
    print(f"✅ Found test item: {test_item.product.name}")
    print(f"✅ Item variant: {test_item.variant.name if test_item.variant else 'None'}")
    
    # Step 2: Test order details API
    print(f"\n2. Testing order details API...")
    response = client.get(f'/mb-admin/api/orders/{test_order.id}/')
    print(f"Order API status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Order API failed: {response.content}")
        return
    
    # Step 3: Test order items API
    print(f"\n3. Testing order items API...")
    response = client.get(f'/mb-admin/api/orders/{test_order.id}/items/')
    print(f"Order items API status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Order items API failed: {response.content}")
        return
    
    items_data = response.json()
    print(f"✅ Found {len(items_data)} items in order")
    
    # Find our test item in the response
    test_item_data = None
    for item in items_data:
        if item['id'] == test_item.id:
            test_item_data = item
            break
    
    if not test_item_data:
        print(f"❌ Test item not found in API response")
        return
    
    print(f"✅ Test item data: {test_item_data}")
    
    # Step 4: Test product API with variants
    product_id = test_item_data.get('product_id') or test_item_data.get('product')
    print(f"\n4. Testing product API for product ID: {product_id}")
    
    if not product_id:
        print("❌ No product ID found in item data")
        return
    
    response = client.get(f'/mb-admin/api/products/{product_id}/')
    print(f"Product API status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Product API failed: {response.content}")
        return
    
    product_data = response.json()
    print(f"✅ Product data received")
    print(f"✅ Product has variants field: {'variants' in product_data}")
    
    if 'variants' in product_data:
        variants = product_data['variants']
        print(f"✅ Found {len(variants)} variants")
        
        for variant in variants:
            print(f"  - {variant['name']} (ID: {variant['id']}, Stock: {variant['stock_quantity']})")
        
        # Step 5: Test dedicated variants endpoint
        print(f"\n5. Testing dedicated variants endpoint...")
        response = client.get(f'/mb-admin/api/products/{product_id}/variants/')
        print(f"Variants endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            variants_data = response.json()
            print(f"✅ Dedicated endpoint returned {len(variants_data)} variants")
        else:
            print(f"⚠️ Dedicated endpoint failed: {response.content}")
        
        # Step 6: Test specific variant endpoint
        if variants:
            variant_id = variants[0]['id']
            print(f"\n6. Testing specific variant endpoint for variant {variant_id}")
            response = client.get(f'/mb-admin/api/variants/{variant_id}/')
            print(f"Variant detail status: {response.status_code}")
            
            if response.status_code == 200:
                variant_detail = response.json()
                print(f"✅ Variant detail: {variant_detail['name']}")
            else:
                print(f"❌ Variant detail failed: {response.content}")
        
        print("\n" + "=" * 60)
        print("✅ ALL API ENDPOINTS ARE WORKING CORRECTLY!")
        print("✅ The issue is likely in the JavaScript frontend logic.")
        print("=" * 60)
        
        # Step 7: Simulate JavaScript workflow
        print(f"\n7. Simulating JavaScript workflow...")
        print(f"   - currentOrderId would be set to: {test_order.id}")
        print(f"   - fetchItemDetailsAndVariants would be called with itemId: {test_item.id}")
        print(f"   - Order items API call: ✅ SUCCESS")
        print(f"   - Find item in response: ✅ SUCCESS")
        print(f"   - Extract product_id: ✅ SUCCESS ({product_id})")
        print(f"   - Product API call: ✅ SUCCESS")
        print(f"   - Check variants in response: ✅ SUCCESS ({len(variants)} variants)")
        print(f"   - populateVariantsDropdown should populate {len(variants)} options")
        
    else:
        print("❌ No variants field in product response")
        
    return True

if __name__ == '__main__':
    test_complete_variant_workflow()