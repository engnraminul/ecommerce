#!/usr/bin/env python3
"""
Test script to verify guest ordering functionality
"""
import requests
import json

# Server URL
BASE_URL = 'http://127.0.0.1:8000'

def test_guest_ordering():
    """Test the complete guest ordering workflow"""
    print("🛒 Testing Guest Ordering Functionality")
    print("=" * 50)
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Step 1: Get CSRF Token by visiting the home page
    print("1. Getting CSRF token...")
    response = session.get(f"{BASE_URL}/")
    if response.status_code == 200:
        print("   ✅ Home page accessible")
        # Extract CSRF token from cookies
        csrf_token = session.cookies.get('csrftoken')
        if csrf_token:
            print(f"   ✅ CSRF token obtained: {csrf_token[:10]}...")
        else:
            print("   ⚠️  CSRF token not found in cookies")
    else:
        print(f"   ❌ Failed to access home page: {response.status_code}")
        return
    
    # Step 2: Try to access products page
    print("\n2. Accessing products...")
    response = session.get(f"{BASE_URL}/products/")
    if response.status_code == 200:
        print("   ✅ Products page accessible")
    else:
        print(f"   ❌ Failed to access products: {response.status_code}")
    
    # Step 3: Test adding item to cart (guest)
    print("\n3. Testing guest cart functionality...")
    
    # Try to add a product to cart (assuming product ID 1 exists)
    cart_data = {
        "product_id": 1,
        "quantity": 1
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token,
        'Referer': f"{BASE_URL}/"
    }
    
    response = session.post(f"{BASE_URL}/api/v1/cart/add/", 
                           json=cart_data, 
                           headers=headers)
    
    print(f"   Cart add response: {response.status_code}")
    if response.status_code == 200:
        try:
            result = response.json()
            print(f"   ✅ Item added to cart: {result}")
        except:
            print("   ✅ Item added to cart (no JSON response)")
    else:
        print(f"   Response content: {response.text[:200]}")
    
    # Step 4: Check cart contents
    print("\n4. Checking cart contents...")
    response = session.get(f"{BASE_URL}/api/v1/cart/", headers=headers)
    
    if response.status_code == 200:
        try:
            cart_data = response.json()
            print(f"   ✅ Cart retrieved: {cart_data.get('total_items', 0)} items")
            if cart_data.get('items'):
                print(f"   ✅ Cart has items: {len(cart_data['items'])}")
            else:
                print("   ⚠️  Cart is empty")
        except:
            print("   ⚠️  Cart response not JSON")
    else:
        print(f"   ❌ Failed to get cart: {response.status_code}")
    
    # Step 5: Test checkout page access (this was the main issue)
    print("\n5. Testing checkout page access (main issue)...")
    response = session.get(f"{BASE_URL}/checkout/")
    
    if response.status_code == 200:
        print("   ✅ Checkout page accessible for guests!")
        print("   ✅ Guest ordering is working!")
    elif response.status_code == 302:
        location = response.headers.get('Location', '')
        if 'login' in location:
            print(f"   ❌ Still redirecting to login: {location}")
            print("   ❌ Guest ordering NOT working")
        else:
            print(f"   ⚠️  Redirected to: {location}")
    else:
        print(f"   ❌ Checkout failed: {response.status_code}")
    
    # Step 6: Test Buy Now button workflow
    print("\n6. Testing Buy Now workflow...")
    
    # First clear cart and add item again
    session.post(f"{BASE_URL}/api/v1/cart/clear/", headers=headers)
    session.post(f"{BASE_URL}/api/v1/cart/add/", json=cart_data, headers=headers)
    
    # Now test accessing checkout directly (Buy Now workflow)
    response = session.get(f"{BASE_URL}/checkout/")
    if response.status_code == 200:
        print("   ✅ Buy Now → Checkout workflow working!")
    else:
        print(f"   ❌ Buy Now workflow failed: {response.status_code}")
    
    print("\n" + "=" * 50)
    print("🏁 Guest Ordering Test Complete")

if __name__ == "__main__":
    test_guest_ordering()
