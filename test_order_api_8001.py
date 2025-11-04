#!/usr/bin/env python
import requests
import json

# Test the order details API with authentication
url = "http://127.0.0.1:8000/mb-admin/api/orders/"

# Since the dashboard works, let's try without authentication first
try:
    response = requests.get(url)
    print(f"Orders API status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("=== ORDERS LIST API SUCCESS ===")
        
        # Find an order with coupon
        for order in data.get('results', [])[:5]:  # Check first 5 orders
            if order.get('order_number') in ['MB1050', 'MB1051', 'MB1049', 'MB1047', 'MB1046', 'MB1045']:
                print(f"\nOrder: {order.get('order_number')}")
                print(f"Coupon Code: {order.get('coupon_code', 'NOT INCLUDED')}")
                print(f"Coupon Discount: {order.get('coupon_discount', 'NOT INCLUDED')}")
                print(f"Subtotal: {order.get('subtotal', 'NOT INCLUDED')}")
                print(f"Total: {order.get('total_amount')}")
                
                # Test order details API
                order_id = order.get('id')
                detail_url = f"http://127.0.0.1:8000/mb-admin/api/orders/{order_id}/"
                detail_response = requests.get(detail_url)
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    print(f"\n=== ORDER DETAILS API FOR {order.get('order_number')} ===")
                    print(f"Coupon Code: {detail_data.get('coupon_code', 'NOT INCLUDED')}")
                    print(f"Coupon Discount: {detail_data.get('coupon_discount', 'NOT INCLUDED')}")
                    print(f"Subtotal: {detail_data.get('subtotal', 'NOT INCLUDED')}")
                    print(f"Total: {detail_data.get('total_amount')}")
                else:
                    print(f"Order details API failed: {detail_response.status_code}")
                break
    else:
        print(f"API Response: {response.text}")
        
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")