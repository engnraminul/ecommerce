#!/usr/bin/env python
"""
Debug script to test stock API endpoints directly
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints():
    """Test the stock API endpoints without authentication first"""
    print("🔍 Testing Stock API Endpoints")
    print("=" * 50)
    
    # Test endpoints that might work without auth
    endpoints = [
        "/mb-admin/",
        "/mb-admin/api/",
        "/mb-admin/api/stock/",
        "/mb-admin/api/stock/stock_summary/",
        "/mb-admin/api/stock-variants/",
    ]
    
    for endpoint in endpoints:
        url = BASE_URL + endpoint
        try:
            print(f"\n📍 Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"   Response: JSON with {len(data)} keys")
                        if 'results' in data:
                            print(f"   Results: {len(data['results'])} items")
                    elif isinstance(data, list):
                        print(f"   Response: JSON list with {len(data)} items")
                    else:
                        print(f"   Response: {type(data)}")
                except:
                    # Not JSON, probably HTML
                    if 'html' in response.headers.get('content-type', '').lower():
                        print("   Response: HTML page")
                    else:
                        print(f"   Response: {response.headers.get('content-type', 'unknown')}")
            
            elif response.status_code == 401:
                print("   Error: Authentication required")
            elif response.status_code == 403:
                print("   Error: Permission denied")
            elif response.status_code == 404:
                print("   Error: Not found")
            else:
                print(f"   Error: {response.status_code}")
                
        except requests.ConnectionError:
            print("   Error: Connection failed (server not running?)")
        except requests.Timeout:
            print("   Error: Request timeout")
        except Exception as e:
            print(f"   Error: {e}")

def check_django_urls():
    """Check if Django URL routing is working"""
    print("\n🔗 Checking Django URL Routing")
    print("=" * 30)
    
    try:
        # Check main dashboard
        response = requests.get(f"{BASE_URL}/mb-admin/", timeout=5)
        print(f"Dashboard (/mb-admin/): {response.status_code}")
        
        # Check if we get redirected to login
        if response.status_code == 302:
            print("   Redirected (probably to login) ✓")
        elif response.status_code == 200:
            print("   Direct access allowed ✓")
        
        # Check stock page
        response = requests.get(f"{BASE_URL}/mb-admin/stock/", timeout=5)
        print(f"Stock page (/mb-admin/stock/): {response.status_code}")
        
        if response.status_code == 302:
            print("   Redirected (probably to login) ✓")
        elif response.status_code == 200:
            print("   Direct access allowed ✓")
            
    except Exception as e:
        print(f"Error checking URLs: {e}")

def check_products_exist():
    """Check if products exist in the database using Django ORM"""
    print("\n📦 Checking Database Products")
    print("=" * 30)
    
    try:
        import os
        import sys
        import django
        
        # Set up Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
        django.setup()
        
        from products.models import Product, ProductVariant, Category
        
        # Count products
        total_products = Product.objects.count()
        tracked_products = Product.objects.filter(track_inventory=True).count()
        categories = Category.objects.count()
        variants = ProductVariant.objects.count()
        
        print(f"Total Products: {total_products}")
        print(f"Tracked Products: {tracked_products}")
        print(f"Categories: {categories}")
        print(f"Variants: {variants}")
        
        if tracked_products > 0:
            print("\n📋 Sample Products:")
            for product in Product.objects.filter(track_inventory=True)[:5]:
                print(f"   - {product.name} (Stock: {product.stock_quantity})")
        else:
            print("❌ No tracked products found!")
            
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_django_urls()
    test_api_endpoints()
    check_products_exist()