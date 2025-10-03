#!/usr/bin/env python3
"""
Simple test script to verify checkout customization is working
"""

import requests
import json
import sys

def test_checkout_customization():
    base_url = "http://127.0.0.1:8000"
    
    print("Testing Checkout Customization API...")
    
    # Test 1: Get active settings (public endpoint)
    try:
        print("\n1. Testing public checkout customization endpoint...")
        response = requests.get(f"{base_url}/api/v1/checkout-customization/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Public API working!")
            print(f"Settings exist: {data.get('success', False)}")
            if data.get('settings'):
                settings = data['settings']
                print(f"Page Title: {settings.get('page_title', 'Default')}")
                print(f"Primary Color: {settings.get('primary_color', '#930000')}")
                print(f"Place Order Button: {settings.get('place_order_button_text', 'Place Order')}")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Test 2: Test checkout page (verify template loads)
    try:
        print("\n2. Testing checkout page template...")
        response = requests.get(f"{base_url}/checkout/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Checkout page loads successfully!")
            
            # Check if customization is working by looking for template variables
            template_checks = [
                ("checkout_customization", "Template variables present"),
                ("page-title", "Page title element present"),
                ("Place Order", "Place Order button found")
            ]
            
            customization_working = 0
            for check_text, description in template_checks:
                if check_text in response.text:
                    print(f"✅ {description}")
                    customization_working += 1
                else:
                    print(f"⚠️  {description} - not found")
            
            if customization_working >= 2:
                print("✅ Checkout customization appears to be working!")
            else:
                print("⚠️  Checkout customization may not be fully working")
        else:
            print(f"❌ Error loading checkout page: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "="*50)
    print("Test Summary:")
    print("If both tests show ✅, the checkout customization is working!")
    print("Next steps:")
    print("1. Visit http://127.0.0.1:8000/dashboard/settings/ to configure")
    print("2. Visit http://127.0.0.1:8000/checkout/ to see the result")
    print("="*50)

if __name__ == "__main__":
    test_checkout_customization()