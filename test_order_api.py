#!/usr/bin/env python
import requests
import json

# Test the API endpoint that the dashboard uses to get order details
order_id = 73  # Let's find the ID for MB1050

# First, let's get all orders to find the correct ID
url = "http://127.0.0.1:8000/mb-admin/api/orders/"

try:
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("=== ORDERS LIST ===")
        
        # Find MB1050
        mb1050_order = None
        for order in data.get('results', []):
            if order.get('order_number') == 'MB1050':
                mb1050_order = order
                print(f"Found MB1050 with ID: {order.get('id')}")
                break
        
        if mb1050_order:
            order_id = mb1050_order['id']
            print(f"\n=== TESTING ORDER DETAILS API FOR ID {order_id} ===")
            
            # Now test the specific order details endpoint
            detail_url = f"http://127.0.0.1:8000/mb-admin/api/orders/{order_id}/"
            detail_response = requests.get(detail_url)
            
            if detail_response.status_code == 200:
                order_data = detail_response.json()
                print(json.dumps(order_data, indent=2))
                
                print("\n=== COUPON INFORMATION ===")
                print(f"Coupon Code: {order_data.get('coupon_code', 'N/A')}")
                print(f"Coupon Discount: {order_data.get('coupon_discount', 'N/A')}")
                print(f"Subtotal: {order_data.get('subtotal', 'N/A')}")
                print(f"Total Amount: {order_data.get('total_amount', 'N/A')}")
            else:
                print(f"Order details API failed with status: {detail_response.status_code}")
                print(f"Response: {detail_response.text}")
        else:
            print("MB1050 not found in orders list")
        
    else:
        print(f"Orders list API failed with status: {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")