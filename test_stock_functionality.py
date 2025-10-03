"""
Test script to verify the stock management functionality is working correctly.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_stock_endpoints():
    """Test the stock management API endpoints"""
    print("🧪 Testing Stock Management API Endpoints...")
    
    # Test dashboard access
    try:
        print("\n1. Testing Dashboard Access...")
        dashboard_url = f"{BASE_URL}/mb-admin/"
        response = requests.get(dashboard_url)
        print(f"   Dashboard status: {response.status_code}")
        
        # Test stock page access
        print("\n2. Testing Stock Page Access...")
        stock_url = f"{BASE_URL}/mb-admin/stock/"
        response = requests.get(stock_url)
        print(f"   Stock page status: {response.status_code}")
        
        # Test stock summary endpoint
        print("\n3. Testing Stock Summary API...")
        summary_url = f"{BASE_URL}/mb-admin/api/stock/stock_summary/"
        response = requests.get(summary_url)
        print(f"   Summary API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total products: {data.get('total_products', 'N/A')}")
            print(f"   Low stock products: {data.get('low_stock_products', 'N/A')}")
            print(f"   Out of stock products: {data.get('out_of_stock_products', 'N/A')}")
            print(f"   Total stock value: ৳{data.get('total_stock_value', 'N/A')}")
        
        # Test stock list endpoint
        print("\n4. Testing Stock List API...")
        stock_list_url = f"{BASE_URL}/mb-admin/api/stock/"
        response = requests.get(stock_list_url)
        print(f"   Stock list API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            products = data.get('results', data) if isinstance(data, dict) else data
            print(f"   Found {len(products) if isinstance(products, list) else 'N/A'} products")
            if isinstance(products, list) and products:
                sample_product = products[0]
                print(f"   Sample product: {sample_product.get('name', 'N/A')}")
                print(f"   Stock quantity: {sample_product.get('stock_quantity', 'N/A')}")
        
        # Test variant list endpoint
        print("\n5. Testing Variant List API...")
        variant_list_url = f"{BASE_URL}/mb-admin/api/stock-variants/"
        response = requests.get(variant_list_url)
        print(f"   Variant list API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            variants = data.get('results', data) if isinstance(data, dict) else data
            print(f"   Found {len(variants) if isinstance(variants, list) else 'N/A'} variants")
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def test_search_functionality():
    """Test the search functionality"""
    print("\n🔍 Testing Search Functionality...")
    
    try:
        # Test search by name
        search_url = f"{BASE_URL}/mb-admin/api/stock/?search=Smartphone"
        response = requests.get(search_url)
        print(f"   Search by name status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            products = data.get('results', data) if isinstance(data, dict) else data
            print(f"   Search results: {len(products) if isinstance(products, list) else 'N/A'} products")
        
        # Test low stock filter
        low_stock_url = f"{BASE_URL}/mb-admin/api/stock/?low_stock=true"
        response = requests.get(low_stock_url)
        print(f"   Low stock filter status: {response.status_code}")
        
        print("✅ Search tests completed!")
        
    except Exception as e:
        print(f"❌ Error during search testing: {e}")

if __name__ == "__main__":
    print("🚀 Starting Stock Management Testing...")
    test_stock_endpoints()
    test_search_functionality()
    print("\n🎉 Testing completed! Please check the Django server logs for any errors.")
    print("\n💡 Next steps:")
    print("   1. Visit http://127.0.0.1:8000/mb-admin/ in your browser")
    print("   2. Login with your admin credentials")
    print("   3. Click on the 'Stock' tab to test the full interface")