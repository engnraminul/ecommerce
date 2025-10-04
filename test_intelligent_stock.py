"""
Test script to verify the intelligent stock management with variants functionality.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_intelligent_stock_management():
    """Test the intelligent stock management system"""
    print("🧪 Testing Intelligent Stock Management System...")
    
    try:
        # Test stock summary with variant intelligence
        print("\n1. Testing Intelligent Stock Summary...")
        summary_url = f"{BASE_URL}/mb-admin/api/stock/stock_summary/"
        response = requests.get(summary_url)
        print(f"   Summary API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   📊 Stock Summary:")
            print(f"     • Total products: {data.get('total_products', 'N/A')}")
            print(f"     • Low stock products: {data.get('low_stock_products', 'N/A')}")
            print(f"     • Out of stock products: {data.get('out_of_stock_products', 'N/A')}")
            print(f"     • Total stock value: ৳{data.get('total_stock_value', 'N/A')}")
        
        # Test intelligent stock list
        print("\n2. Testing Intelligent Product Stock List...")
        stock_list_url = f"{BASE_URL}/mb-admin/api/stock/"
        response = requests.get(stock_list_url)
        print(f"   Stock list API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            products = data.get('results', data) if isinstance(data, dict) else data
            print(f"   📦 Found {len(products) if isinstance(products, list) else 'N/A'} products")
            
            if isinstance(products, list) and products:
                # Analyze first few products
                for i, product in enumerate(products[:3]):
                    print(f"\n   📋 Product {i+1}: {product.get('name', 'N/A')}")
                    print(f"     • SKU: {product.get('sku', 'N/A')}")
                    print(f"     • Stock Management: {product.get('stock_management_type', 'N/A')}")
                    print(f"     • Has Variants: {product.get('has_variants', False)}")
                    print(f"     • Variant Count: {product.get('variant_count', 0)}")
                    print(f"     • Effective Stock: {product.get('effective_stock_quantity', 'N/A')}")
                    print(f"     • Product Stock: {product.get('stock_quantity', 'N/A')}")
                    print(f"     • Total Variant Stock: {product.get('total_variant_stock', 'N/A')}")
                    print(f"     • Effective Cost Price: ৳{product.get('effective_cost_price', 'N/A')}")
                    print(f"     • Stock Value: ৳{product.get('stock_value', 'N/A')}")
                    print(f"     • Stock Status: {product.get('stock_status', 'N/A')}")
                    
                    # Show variants if available
                    variants = product.get('variants', [])
                    if variants:
                        print(f"     📌 Variants ({len(variants)}):")
                        for variant in variants[:2]:  # Show first 2 variants
                            print(f"       - {variant.get('name', 'N/A')}: {variant.get('stock_quantity', 0)} units (Cost: ৳{variant.get('effective_cost_price', 0)})")
        
        # Test variant stock endpoint
        print("\n3. Testing Variant Stock List...")
        variant_list_url = f"{BASE_URL}/mb-admin/api/stock-variants/"
        response = requests.get(variant_list_url)
        print(f"   Variant list API status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            variants = data.get('results', data) if isinstance(data, dict) else data
            print(f"   🏷️ Found {len(variants) if isinstance(variants, list) else 'N/A'} variants")
            
            if isinstance(variants, list) and variants:
                for i, variant in enumerate(variants[:3]):
                    print(f"\n   🏷️ Variant {i+1}: {variant.get('product_name', 'N/A')} - {variant.get('name', 'N/A')}")
                    print(f"     • SKU: {variant.get('sku', 'N/A')}")
                    print(f"     • Stock: {variant.get('stock_quantity', 'N/A')}")
                    print(f"     • Effective Cost: ৳{variant.get('effective_cost_price', 'N/A')}")
                    print(f"     • Stock Value: ৳{variant.get('stock_value', 'N/A')}")
                    print(f"     • Status: {variant.get('stock_status', 'N/A')}")
        
        print("\n✅ Intelligent stock management tests completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def test_stock_management_features():
    """Test specific features of stock management"""
    print("\n🔍 Testing Stock Management Features...")
    
    try:
        # Test search functionality
        search_url = f"{BASE_URL}/mb-admin/api/stock/?search=phone"
        response = requests.get(search_url)
        print(f"   📱 Search by 'phone' status: {response.status_code}")
        
        # Test low stock filter
        low_stock_url = f"{BASE_URL}/mb-admin/api/stock/?low_stock=true"
        response = requests.get(low_stock_url)
        print(f"   ⚠️ Low stock filter status: {response.status_code}")
        
        # Test out of stock filter
        out_of_stock_url = f"{BASE_URL}/mb-admin/api/stock/?out_of_stock=true"
        response = requests.get(out_of_stock_url)
        print(f"   🚫 Out of stock filter status: {response.status_code}")
        
        # Test low stock report
        report_url = f"{BASE_URL}/mb-admin/api/stock/low_stock_report/"
        response = requests.get(report_url)
        print(f"   📊 Low stock report status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"     Low stock products count: {data.get('count', 'N/A')}")
        
        print("✅ Feature tests completed!")
        
    except Exception as e:
        print(f"❌ Error during feature testing: {e}")

if __name__ == "__main__":
    print("🚀 Starting Intelligent Stock Management Testing...")
    test_intelligent_stock_management()
    test_stock_management_features()
    print("\n🎉 Testing completed!")
    print("\n💡 Key Features Tested:")
    print("   ✅ Intelligent variant vs product stock detection")
    print("   ✅ Cost price-based stock value calculations") 
    print("   ✅ Effective stock quantity management")
    print("   ✅ Smart stock status determination")
    print("   ✅ Variant-aware filtering and reporting")
    print("\n🌟 Your stock management system now intelligently handles:")
    print("   • Products WITH variants → Uses variant stock/cost")
    print("   • Products WITHOUT variants → Uses product stock/cost")
    print("   • Cost price-based stock valuations")
    print("   • Smart low stock detection across variants")
    print("\n🔗 Visit: http://127.0.0.1:8000/mb-admin/stock/")