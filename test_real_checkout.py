#!/usr/bin/env python
import requests

def test_real_checkout():
    try:
        print("Testing real checkout page...")
        
        # Test accessing checkout directly (should redirect to cart if empty)
        response = requests.get("http://127.0.0.1:8000/checkout/", allow_redirects=False)
        print(f"Checkout Status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"Redirected to: {response.headers.get('Location', 'Unknown')}")
            print("✅ Checkout correctly redirects when cart is empty")
        elif response.status_code == 200:
            print("✅ Checkout page loads directly")
            
            # Check if template variables are working
            content = response.text
            if "Checkout" in content and "Place Order" in content:
                print("✅ Checkout customization working!")
                
                # Save the output
                with open("real_checkout_output.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("✅ Saved output to real_checkout_output.html")
        
        # Also test the API endpoint
        print("\n" + "-"*30)
        api_response = requests.get("http://127.0.0.1:8000/api/v1/checkout-customization/")
        if api_response.status_code == 200:
            data = api_response.json()
            print("✅ API Endpoint working")
            print(f"   Settings available: {len(data.get('settings', {}))}")
            print(f"   Page title: {data['settings'].get('page_title', 'N/A')}")
        else:
            print(f"❌ API Endpoint failed: {api_response.status_code}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_real_checkout()