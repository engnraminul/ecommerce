#!/usr/bin/env python
import requests

def test_checkout_template_direct():
    try:
        print("Testing checkout template directly...")
        
        response = requests.get("http://127.0.0.1:8000/test-checkout/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Save for inspection
            with open("test_checkout_direct.html", "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ Template rendered, saved to test_checkout_direct.html")
            
            # Check for customization
            customization_count = content.count("checkout_customization")
            print(f"📊 checkout_customization references: {customization_count}")
            
            # Check for specific customized content
            checks = [
                ("checkout_customization", "Template variables"),
                ("Checkout", "Page title"),
                ("Complete your order", "Subtitle"),
                ("Place Order", "Button text")
            ]
            
            for search_text, description in checks:
                if search_text in content:
                    print(f"✅ {description}: Found")
                else:
                    print(f"❌ {description}: Not found")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_checkout_template_direct()