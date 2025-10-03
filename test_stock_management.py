#!/usr/bin/env python
"""
Test script for Stock Management API endpoints
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:8000"
API_BASE = f"{BASE_URL}/mb-admin/api"

# Test credentials (replace with actual admin credentials)
# You'll need to get these from your dashboard login
USERNAME = "admin"  # Replace with actual username
PASSWORD = "admin"  # Replace with actual password

def test_stock_api():
    """Test all stock management API endpoints"""
    session = requests.Session()
    
    # Get CSRF token and login
    print("🔐 Testing authentication...")
    login_page = session.get(f"{BASE_URL}/mb-admin/login/")
    csrf_token = None
    
    # Extract CSRF token from login page
    for line in login_page.text.split('\n'):
        if 'csrfmiddlewaretoken' in line and 'value=' in line:
            csrf_token = line.split('value="')[1].split('"')[0]
            break
    
    if not csrf_token:
        print("❌ Could not extract CSRF token")
        return
    
    # Login attempt (you may need to adjust this based on your login form)
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'csrfmiddlewaretoken': csrf_token
    }
    
    login_response = session.post(f"{BASE_URL}/mb-admin/login/", data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed with status {login_response.status_code}")
        return
    
    print("✅ Authentication successful")
    
    # Test 1: Stock Summary
    print("\n📊 Testing stock summary...")
    try:
        response = session.get(f"{API_BASE}/stock/stock_summary/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stock Summary: {data['total_products']} products, {data['low_stock_products']} low stock")
        else:
            print(f"❌ Stock summary failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stock summary error: {e}")
    
    # Test 2: Stock List
    print("\n📋 Testing stock list...")
    try:
        response = session.get(f"{API_BASE}/stock/")
        if response.status_code == 200:
            data = response.json()
            products = data.get('results', data) if isinstance(data, dict) else data
            print(f"✅ Stock List: Found {len(products)} products")
            
            # Store first product ID for adjustment test
            if products:
                first_product = products[0]
                product_id = first_product['id']
                current_stock = first_product['stock_quantity']
                
                # Test 3: Stock Adjustment
                print(f"\n🔧 Testing stock adjustment for product {product_id}...")
                adjustment_data = {
                    'action': 'increase',
                    'quantity': 1,
                    'reason': 'API test adjustment'
                }
                
                try:
                    adj_response = session.post(f"{API_BASE}/stock/{product_id}/adjust_stock/", data=adjustment_data)
                    if adj_response.status_code == 200:
                        adj_data = adj_response.json()
                        if adj_data.get('success'):
                            print(f"✅ Stock Adjustment: {adj_data['old_stock']} → {adj_data['new_stock']}")
                        else:
                            print(f"❌ Stock adjustment failed: {adj_data}")
                    else:
                        print(f"❌ Stock adjustment failed: {adj_response.status_code}")
                except Exception as e:
                    print(f"❌ Stock adjustment error: {e}")
        else:
            print(f"❌ Stock list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stock list error: {e}")
    
    # Test 4: Variant Stock List
    print("\n🔀 Testing variant stock list...")
    try:
        response = session.get(f"{API_BASE}/stock-variants/")
        if response.status_code == 200:
            data = response.json()
            variants = data.get('results', data) if isinstance(data, dict) else data
            print(f"✅ Variant Stock List: Found {len(variants)} variants")
        else:
            print(f"❌ Variant stock list failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Variant stock list error: {e}")
    
    # Test 5: Low Stock Report
    print("\n⚠️ Testing low stock report...")
    try:
        response = session.get(f"{API_BASE}/stock/low_stock_report/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Low Stock Report: {data['count']} products with low stock")
        else:
            print(f"❌ Low stock report failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Low stock report error: {e}")
    
    print("\n🎉 API testing completed!")

def test_ui_accessibility():
    """Test if the stock management UI is accessible"""
    print("\n🌐 Testing UI accessibility...")
    
    try:
        response = requests.get(f"{BASE_URL}/mb-admin/stock/")
        if response.status_code == 200:
            # Check for key elements in the HTML
            html = response.text
            checks = [
                ('Stock Management title', 'Stock Management'),
                ('Stock summary cards', 'Total Products'),
                ('Stock table', 'stockTable'),
                ('Bulk adjust button', 'Bulk Adjust'),
                ('Export button', 'Export CSV'),
                ('Stock adjustment modal', 'stockAdjustmentModal')
            ]
            
            for check_name, check_text in checks:
                if check_text in html:
                    print(f"✅ {check_name}: Found")
                else:
                    print(f"❌ {check_name}: Missing")
        else:
            print(f"❌ UI accessibility test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ UI accessibility error: {e}")

if __name__ == "__main__":
    print("🧪 Stock Management System Test Suite")
    print("=" * 50)
    
    # Test UI first (doesn't require login)
    test_ui_accessibility()
    
    # Test API endpoints (requires login)
    print(f"\n📝 Note: For API tests, please ensure you have admin credentials")
    print(f"   Username: {USERNAME}")
    print(f"   Password: {PASSWORD}")
    print(f"   Server: {BASE_URL}")
    
    test_api = input("\nDo you want to run API tests? (y/n): ").lower().strip()
    if test_api == 'y':
        test_stock_api()
    else:
        print("Skipping API tests.")
    
    print("\n✨ Test suite completed!")