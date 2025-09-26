#!/usr/bin/env python
"""
Quick test script to verify the statistics API is working
"""
import os
import sys
import django
import requests

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

def test_statistics_api():
    print("Testing Statistics API...")
    
    # Create Django test client
    client = Client()
    
    # Try to find an admin user
    admin_user = User.objects.filter(is_staff=True).first()
    
    if not admin_user:
        print("❌ No admin user found. Cannot test the API.")
        return False
    
    print(f"✅ Found admin user: {admin_user.username}")
    
    # Login as admin user
    client.force_login(admin_user)
    
    # Make request to statistics API
    response = client.get('/api/dashboard/statistics/', SERVER_NAME='testserver')
    
    print(f"📊 API Response Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print("✅ Statistics API is working successfully!")
            print(f"📈 Total Sales: ${data.get('total_sales', 0)}")
            print(f"📦 Total Orders: {data.get('orders_count', 0)}")
            print(f"💰 Total Revenue: ${data.get('total_revenue', 0)}")
            print(f"💸 Total Expenses: ${data.get('total_expenses', 0)}")
            return True
        except Exception as e:
            print(f"❌ Error parsing JSON response: {e}")
            print(f"Response content: {response.content}")
            return False
    else:
        print(f"❌ API returned error status: {response.status_code}")
        print(f"Response: {response.content}")
        return False

if __name__ == "__main__":
    try:
        success = test_statistics_api()
        if success:
            print("\n🎉 Statistics API test completed successfully!")
        else:
            print("\n💥 Statistics API test failed!")
    except Exception as e:
        print(f"\n💥 Test script error: {e}")
        import traceback
        traceback.print_exc()