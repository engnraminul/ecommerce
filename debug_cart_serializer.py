#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth import get_user_model
from cart.models import Cart, CartItem
from cart.serializers import CartSerializer

# Test the cart serializer specifically
User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

if admin_user:
    try:
        cart, created = Cart.objects.get_or_create(user=admin_user)
        print(f"Cart found/created: {cart.id}")
        
        cart_items = cart.items.all()
        print(f"Cart has {cart_items.count()} items")
        
        for item in cart_items[:3]:  # Check first 3 items
            print(f"\nItem {item.id}: {item.product.name}")
            print(f"  Has variant: {item.variant is not None}")
            if item.variant:
                print(f"  Variant image: {item.variant.image}")
                print(f"  Variant image_url: {item.variant.image_url}")
            
            # Check product images
            product_images = item.product.images.all()
            print(f"  Product has {product_images.count()} images")
            for img in product_images:
                print(f"    Image: {img.image}")
                print(f"    Is primary: {img.is_primary}")
                
        # Test serializer on a single item
        if cart_items.exists():
            print("\nTesting CartSerializer...")
            from django.http import HttpRequest
            request = HttpRequest()
            request.user = admin_user
            
            context = {'request': request}
            serializer = CartSerializer(cart, context=context)
            try:
                data = serializer.data
                print("Serializer success!")
                print(f"Cart total: {data.get('total_amount', 'N/A')}")
                print(f"Items count: {len(data.get('items', []))}")
            except Exception as e:
                print(f"Serializer error: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No admin user found")