#!/usr/bin/env python
import requests
import json

def test_checkout_with_cart():
    base_url = "http://127.0.0.1:8000"
    session = requests.Session()
    
    try:
        print("1. Getting CSRF token...")
        # Get CSRF token from any page
        response = session.get(f"{base_url}/")
        csrf_token = None
        if 'csrftoken' in session.cookies:
            csrf_token = session.cookies['csrftoken']
        
        print(f"CSRF Token: {csrf_token}")
        
        print("\n2. Adding item to cart...")
        # Try to add a product to cart (using product ID 18 which exists)
        cart_data = {
            'product_id': 18,
            'quantity': 1,
            'csrfmiddlewaretoken': csrf_token
        }
        
        response = session.post(f"{base_url}/api/v1/cart/add/", data=cart_data)
        print(f"Add to cart status: {response.status_code}")
        
        print("\n3. Accessing checkout page...")
        response = session.get(f"{base_url}/checkout/")
        print(f"Checkout page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Save for inspection
            with open("checkout_with_cart.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Check for checkout customization
            if "checkout_customization" in content:
                print("✅ Template variables found!")
                count = content.count("checkout_customization")
                print(f"   Total references: {count}")
            else:
                print("❌ Template variables not found")
                
            # Check if it's actually the checkout page
            if "Shopping Cart" in content:
                print("⚠️  Still showing cart page")
            elif "Checkout" in content:
                print("✅ Showing checkout page")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_checkout_with_cart()