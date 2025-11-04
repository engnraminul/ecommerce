#!/usr/bin/env python3
"""
Add test items to cart and test checkout functionality
"""

import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test import Client
from products.models import Product
from cart.models import Cart, CartItem

def main():
    print("🛒 Adding test items to cart for checkout testing...")
    
    client = Client()
    
    # Get a product to add to cart
    try:
        product = Product.objects.filter(is_active=True).first()
        if not product:
            print("❌ No active products found. Please add some products first.")
            return
        
        print(f"📱 Found product: {product.name}")
        
        # Add product to cart via API
        response = client.post('/api/v1/cart/add/', {
            'product_id': product.id,
            'quantity': 2
        }, content_type='application/json')
        
        if response.status_code == 200:
            print("✅ Successfully added product to cart")
            
            # Test cart summary
            response = client.get('/api/v1/cart/summary/')
            if response.status_code == 200:
                data = response.json()
                print(f"📊 Cart Summary:")
                print(f"   Items: {len(data['items'])}")
                print(f"   Subtotal: ৳{data['subtotal']}")
                print(f"   Total: ৳{data['total_amount']}")
                print(f"   Coupon: {data['coupon_code'] or 'None'}")
                
                if len(data['items']) > 0:
                    print(f"   First item: {data['items'][0]['product_name']} (qty: {data['items'][0]['quantity']})")
                
                # Test applying a coupon
                print("\n🎫 Testing coupon application...")
                coupon_response = client.post('/api/v1/cart/apply-coupon/', {
                    'code': 'FLAT50'
                }, content_type='application/json')
                
                if coupon_response.status_code == 200:
                    print("✅ Coupon applied successfully!")
                    
                    # Check updated totals
                    updated_response = client.get('/api/v1/cart/summary/')
                    if updated_response.status_code == 200:
                        updated_data = updated_response.json()
                        print(f"📊 Updated Cart Summary:")
                        print(f"   Subtotal: ৳{updated_data['subtotal']}")
                        print(f"   Coupon Discount: -৳{updated_data['coupon_discount']}")
                        print(f"   Total: ৳{updated_data['total_amount']}")
                        print(f"   Applied Coupon: {updated_data['coupon_code']}")
                else:
                    coupon_data = coupon_response.json()
                    print(f"⚠️ Coupon application result: {coupon_data}")
                
            else:
                print(f"❌ Cart summary failed: {response.status_code}")
        else:
            error_data = response.json()
            print(f"❌ Failed to add to cart: {error_data}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🔗 Test the checkout page manually:")
    print("   1. Visit http://localhost:8000/checkout/")
    print("   2. Check if items and totals display correctly")
    print("   3. Test coupon application and removal")
    print("   4. Verify shipping cost calculations")

if __name__ == '__main__':
    main()