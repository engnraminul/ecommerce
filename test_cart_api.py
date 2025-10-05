#!/usr/bin/env python
import os
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.test.client import Client
from django.contrib.auth import get_user_model

# Test the cart API
client = Client()

print("Testing cart API endpoints...")

# Test 1: GET /api/v1/cart/ (without authentication)
try:
    response = client.get('/api/v1/cart/')
    print(f"GET /api/v1/cart/ - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content.decode()[:500]}")
    else:
        print("Response: Success")
except Exception as e:
    print(f"Error testing GET /api/v1/cart/: {e}")

# Test 2: GET /api/v1/cart/ with location parameter
try:
    response = client.get('/api/v1/cart/?location=dhaka')
    print(f"GET /api/v1/cart/?location=dhaka - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content.decode()[:500]}")
    else:
        print("Response: Success")
except Exception as e:
    print(f"Error testing GET /api/v1/cart/ with location: {e}")

# Test 3: Test with authenticated user
User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

if admin_user:
    client.force_login(admin_user)
    try:
        response = client.get('/api/v1/cart/')
        print(f"GET /api/v1/cart/ (authenticated) - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Response content: {response.content.decode()[:500]}")
        else:
            print("Response: Success")
    except Exception as e:
        print(f"Error testing authenticated cart API: {e}")

# Test 4: Check if cart summary endpoint exists
try:
    response = client.get('/api/v1/cart/summary/')
    print(f"GET /api/v1/cart/summary/ - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response content: {response.content.decode()[:500]}")
    else:
        print("Response: Success")
except Exception as e:
    print(f"Error testing cart summary: {e}")

# Test 5: Check missing endpoint /api/cart/preview/
try:
    response = client.get('/api/cart/preview/')
    print(f"GET /api/cart/preview/ - Status: {response.status_code}")
    print("^ This should be 404 - endpoint doesn't exist")
except Exception as e:
    print(f"Error testing cart preview: {e}")

print("\nCart model check:")
from cart.models import Cart
try:
    cart_count = Cart.objects.count()
    print(f"Total carts in database: {cart_count}")
except Exception as e:
    print(f"Error accessing Cart model: {e}")