#!/usr/bin/env python
import requests

def test_checkout_page():
    try:
        response = requests.get("http://127.0.0.1:8000/checkout/")
        if response.status_code == 200:
            print("✅ Checkout page loaded successfully!")
            
            # Save the response to a file for inspection
            with open("checkout_page_output.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✅ Checkout page content saved to checkout_page_output.html")
            
            # Check for key customization elements
            content = response.text
            
            checks = [
                ("checkout_customization", "Template variable found"),
                ("Place Order", "Place order button text"),
                ("page-title", "Page title class"),
                ("Checkout", "Checkout text found"),
                ("Complete your order", "Subtitle text"),
                ("Primary Color", "CSS custom properties")
            ]
            
            for search_text, description in checks:
                if search_text in content:
                    print(f"✅ {description}: Found")
                else:
                    print(f"❌ {description}: Not found")
                    
            # Count total checkout_customization references
            count = content.count("checkout_customization")
            print(f"\n📊 Total 'checkout_customization' references: {count}")
            
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_checkout_page()