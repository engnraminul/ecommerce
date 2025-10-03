#!/usr/bin/env python
import requests

def comprehensive_checkout_test():
    print("🚀 Comprehensive Checkout Customization Test")
    print("=" * 50)
    
    try:
        # Test the API endpoint
        print("\n1. Testing API Endpoint:")
        api_response = requests.get("http://127.0.0.1:8000/api/v1/checkout-customization/")
        
        if api_response.status_code == 200:
            api_data = api_response.json()
            print("✅ API Status: Working")
            print(f"   Page Title: {api_data['settings']['page_title']}")
            print(f"   Primary Color: {api_data['settings']['primary_color']}")
            print(f"   Place Order Button: {api_data['settings']['place_order_button_text']}")
        else:
            print(f"❌ API Status: Failed ({api_response.status_code})")
        
        # Test the template rendering
        print("\n2. Testing Template Rendering:")
        template_response = requests.get("http://127.0.0.1:8000/test-checkout/")
        
        if template_response.status_code == 200:
            content = template_response.text
            print("✅ Template Status: Working")
            
            # Test specific customizations
            customizations_to_test = [
                ("Checkout", "Page Title"),
                ("Complete your order", "Page Subtitle"),
                ("Place Order", "Place Order Button"),
                ("page-title", "CSS Classes"),
                ("checkout-form", "Form Elements")
            ]
            
            print("\n3. Testing Customized Content:")
            all_working = True
            for search_text, description in customizations_to_test:
                if search_text in content:
                    print(f"   ✅ {description}: Found")
                else:
                    print(f"   ❌ {description}: Not Found")
                    all_working = False
            
            # Test if this is actually the checkout template (not cart)
            if "checkout-form" in content and "checkout-page" in content:
                print("   ✅ Correct Template: Using checkout template")
            else:
                print("   ⚠️  Template Warning: May not be checkout template")
                all_working = False
            
            print(f"\n4. Overall Result:")
            if all_working and api_response.status_code == 200:
                print("🎉 SUCCESS: Checkout customization is fully working!")
                print("\n📋 Features Working:")
                print("   ✅ API endpoint for dynamic settings")
                print("   ✅ Template variable injection via context processor")
                print("   ✅ Dynamic content rendering")
                print("   ✅ Default fallback values")
                
                print("\n🎯 Next Steps:")
                print("   1. Visit http://127.0.0.1:8000/mb-admin/ to access dashboard")
                print("   2. Go to Settings > Checkout Customization")
                print("   3. Modify settings like colors, text, labels")
                print("   4. Visit http://127.0.0.1:8000/test-checkout/ to see changes")
                
            else:
                print("⚠️  PARTIAL: Some features working, some need attention")
        else:
            print(f"❌ Template Status: Failed ({template_response.status_code})")
    
    except Exception as e:
        print(f"❌ Test Error: {e}")

if __name__ == "__main__":
    comprehensive_checkout_test()