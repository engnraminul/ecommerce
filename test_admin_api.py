#!/usr/bin/env python3
"""
Test script to verify admin API authentication and order details endpoint
"""
import os
import django
import requests
from bs4 import BeautifulSoup

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

def test_admin_login_and_api():
    print("=== Testing Admin Login and API Access ===")
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get login page for CSRF token
    print("1. Getting login page...")
    login_page = session.get('http://127.0.0.1:8000/mb-admin/login/')
    print(f"   Login page status: {login_page.status_code}")
    
    # Parse CSRF token
    soup = BeautifulSoup(login_page.content, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    if csrf_token:
        csrf_value = csrf_token.get('value')
        print(f"   CSRF token found: {csrf_value[:20]}...")
    else:
        print("   No CSRF token found, trying without it")
        csrf_value = ''
    
    # Step 2: Login
    print("2. Attempting login...")
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_value
    }
    
    login_response = session.post(
        'http://127.0.0.1:8000/mb-admin/login/',
        data=login_data,
        headers={'Referer': 'http://127.0.0.1:8000/mb-admin/login/'}
    )
    print(f"   Login response status: {login_response.status_code}")
    print(f"   Login response URL: {login_response.url}")
    
    # Step 3: Test orders list API
    print("3. Testing orders list API...")
    orders_response = session.get(
        'http://127.0.0.1:8000/mb-admin/api/orders/',
        headers={'Accept': 'application/json'}
    )
    print(f"   Orders API status: {orders_response.status_code}")
    
    if orders_response.status_code == 200:
        orders_data = orders_response.json()
        print(f"   Orders found: {len(orders_data.get('results', orders_data))}")
        
        # Step 4: Test individual order API
        if isinstance(orders_data, dict) and 'results' in orders_data:
            orders_list = orders_data['results']
        else:
            orders_list = orders_data
            
        if orders_list:
            first_order = orders_list[0]
            order_id = first_order['id']
            print(f"4. Testing individual order API (Order ID: {order_id})...")
            
            order_response = session.get(
                f'http://127.0.0.1:8000/mb-admin/api/orders/{order_id}/',
                headers={'Accept': 'application/json'}
            )
            print(f"   Order detail API status: {order_response.status_code}")
            
            if order_response.status_code == 200:
                order_data = order_response.json()
                print(f"   Order number: {order_data.get('order_number')}")
                print(f"   Order status: {order_data.get('status')}")
                print(f"   Customer email: {order_data.get('customer_email')}")
                print(f"   Has shipping address: {bool(order_data.get('shipping_address'))}")
                print(f"   Has items: {bool(order_data.get('items'))}")
                print(f"   Items count: {len(order_data.get('items', []))}")
                
                print("\n=== API TEST SUCCESSFUL ===")
                print("The order details API is working correctly!")
                print("If the popup still shows '-' placeholders, the issue is in the JavaScript.")
                return True
            else:
                print(f"   Order detail API failed: {order_response.text}")
        else:
            print("   No orders found to test individual API")
    else:
        print(f"   Orders API failed: {orders_response.text}")
    
    print("\n=== API TEST FAILED ===")
    return False

if __name__ == "__main__":
    test_admin_login_and_api()