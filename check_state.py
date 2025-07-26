#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from products.models import Product, ProductVariant
from cart.models import Cart, CartItem
from users.models import User

def check_system_state():
    """Check the current state of products, users, and carts"""
    
    print("=== SYSTEM STATE CHECK ===")
    
    # Check products
    products = Product.objects.filter(is_active=True)
    print(f"Active products: {products.count()}")
    
    for product in products[:3]:
        variants = product.variants.all()
        print(f"  - {product.name}: {variants.count()} variants")
    
    # Check users
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    
    for user in users:
        print(f"  - {user.username} ({user.email})")
        
        # Check if user has a cart
        try:
            cart = Cart.objects.get(user=user)
            print(f"    Cart: {cart.items.count()} items")
        except Cart.DoesNotExist:
            print(f"    Cart: None")
    
    print("=== END CHECK ===")

if __name__ == "__main__":
    check_system_state()
